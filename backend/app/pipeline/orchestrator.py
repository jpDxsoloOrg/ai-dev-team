import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.developer import DeveloperAgent
from app.agents.planner import PlannerAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.tester import TesterAgent
from app.models.enums import PipelineStatus, TaskStatus
from app.models.pipeline import PipelineRun, PipelineTask
from app.models.schemas import DeveloperConfig
from app.pipeline.task_assigner import TaskAssigner
from app.providers.base import LLMProvider
from app.pipeline.merge import merge_task_outputs
from app.services.file_manager import write_files, get_workspace_path
from app.services.git_ops import init_repo, create_branch, commit_files, push_branch, is_git_repo
from app.services.project_analyzer import read_task_files, correct_file_paths, analyze_project
from app.ws.events import EventType, PipelineEvent
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

MAX_REVIEW_ROUNDS = 2


class PipelineOrchestrator:
    def __init__(
        self,
        run_id: str,
        goal: str,
        provider: LLMProvider,
        model: str,
        developers: list[DeveloperConfig],
        session_factory,
        pause_event: asyncio.Event,
        project_context: str = "",
        project_path: str = "",
        detected_stack: list[str] | None = None,
        auto_assign: bool = True,
        all_developers: list[DeveloperConfig] | None = None,
    ) -> None:
        self.run_id = run_id
        self.goal = goal
        self.provider = provider
        self.model = model
        self.developers = developers
        self.all_developers = all_developers or developers
        self.session_factory = session_factory
        self.pause_event = pause_event
        self.project_context = project_context
        self.project_path = project_path
        self.detected_stack = detected_stack or []
        self.auto_assign = auto_assign
        self.assigner = TaskAssigner(developers, provider, model)
        # For manual assignment mode
        self._pending_tasks: list[PipelineTask] = []
        self._all_code_outputs: dict[str, dict[str, str]] = {}
        self._manual_ready = asyncio.Event()
        self._waiting_for_manual = False

    async def _broadcast(self, event_type: EventType, data: dict) -> None:
        event = PipelineEvent(type=event_type, run_id=self.run_id, data=data)
        await ws_manager.broadcast(event)

    async def _check_pause(self) -> None:
        await self.pause_event.wait()

    async def _update_run_status(self, session: AsyncSession, status: PipelineStatus) -> None:
        result = await session.execute(select(PipelineRun).where(PipelineRun.id == self.run_id))
        run = result.scalar_one()
        run.status = status.value
        run.updated_at = datetime.now(timezone.utc)
        if status in (PipelineStatus.COMPLETED, PipelineStatus.FAILED):
            run.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await self._broadcast(EventType.PIPELINE_STATUS, {"status": status.value})

    async def manual_assign(self, task_id: str, dev_id: str) -> None:
        """Manually assign a task to a developer and start development immediately."""
        dev_config = next((d for d in self.all_developers if d.id == dev_id), None)
        if dev_config is None:
            raise ValueError(f"Developer {dev_id} not found")

        task = next((t for t in self._pending_tasks if t.id == task_id), None)
        if task is None:
            raise ValueError(f"Task {task_id} not found or not pending")

        self._pending_tasks.remove(task)

        async with self.session_factory() as session:
            # Re-attach the task to this session
            result = await session.execute(select(PipelineTask).where(PipelineTask.id == task_id))
            db_task = result.scalar_one()
            db_task.assigned_to = dev_config.name
            db_task.status = TaskStatus.ASSIGNED.value
            await session.commit()

            await self._broadcast(EventType.TASK_ASSIGNED, {
                "task_id": task_id, "developer": dev_config.name,
                "developer_emoji": dev_config.emoji,
            })

            # Develop immediately
            db_task.status = TaskStatus.IN_PROGRESS.value
            await session.commit()
            await self._broadcast(EventType.TASK_UPDATED, {
                "task_id": task_id, "status": TaskStatus.IN_PROGRESS.value,
            })

            agent = DeveloperAgent(
                self.provider, self.model, self.run_id,
                name=dev_config.name, specialty=dev_config.specialty,
                custom_instructions=dev_config.custom_prompt,
                detected_stack=self.detected_stack,
            )
            task_files: dict[str, str] = {}
            if self.project_path and task.file_paths:
                task_files = read_task_files(self.project_path, task.file_paths)

            files = await agent.develop(
                task.title, task.description,
                self.project_context, task_files,
            )
            self._all_code_outputs[task_id] = files
            db_task.code_output = str(files)
            await session.commit()

            await self._broadcast(EventType.CODE_GENERATED, {
                "agent": dev_config.name,
                "files": list(files.keys()),
                "contents": files,
            })

        # If no more pending tasks, signal the main loop
        if not self._pending_tasks:
            self._manual_ready.set()

    async def toggle_auto_assign(self, enabled: bool) -> None:
        """Toggle auto-assignment. If enabling, assign remaining pending tasks."""
        self.auto_assign = enabled
        logger.info("Auto-assign toggled to %s (%d pending tasks)", enabled, len(self._pending_tasks))

        if enabled and self._pending_tasks:
            # Auto-assign remaining pending tasks
            async with self.session_factory() as session:
                tasks_to_assign = list(self._pending_tasks)
                assignments, still_unassigned = await self._assign_tasks(session, tasks_to_assign)
                self._pending_tasks = still_unassigned

                if assignments:
                    code_outputs = await self._develop(session, assignments)
                    self._all_code_outputs.update(code_outputs)

            if not self._pending_tasks:
                self._manual_ready.set()

    async def run(self) -> None:
        try:
            async with self.session_factory() as session:
                # Phase 1: Planning
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.PLANNING)
                tasks = await self._plan(session)

                if not tasks:
                    await self._update_run_status(session, PipelineStatus.FAILED)
                    return

                if self.auto_assign:
                    # Phase 2+3: Auto-assign and develop in rounds
                    unassigned = list(tasks)

                    while unassigned:
                        await self._check_pause()
                        await self._update_run_status(session, PipelineStatus.ASSIGNING)
                        assignments, still_unassigned = await self._assign_tasks(session, unassigned)

                        if not assignments:
                            for task in still_unassigned:
                                task.status = TaskStatus.FAILED.value
                                await self._broadcast(EventType.TASK_UPDATED, {
                                    "task_id": task.id, "status": "failed",
                                    "reason": "No developer available",
                                })
                            await session.commit()
                            break

                        await self._check_pause()
                        await self._update_run_status(session, PipelineStatus.DEVELOPING)
                        code_outputs = await self._develop(session, assignments)
                        self._all_code_outputs.update(code_outputs)
                        unassigned = still_unassigned
                else:
                    # Manual assignment mode: wait for user to assign tasks
                    await self._update_run_status(session, PipelineStatus.ASSIGNING)
                    self._pending_tasks = list(tasks)
                    self._waiting_for_manual = True

                    await self._broadcast(EventType.LOG, {
                        "message": f"Manual assignment mode: {len(tasks)} tasks waiting for assignment",
                    })

            # Wait outside the session context for manual assignments
            if self._waiting_for_manual:
                await self._manual_ready.wait()
                self._waiting_for_manual = False

            async with self.session_factory() as session:
                # Phase 4: Reviewing
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.REVIEWING)
                approved = await self._review(session, self._all_code_outputs)

                # Phase 5: Testing
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.TESTING)
                await self._test(session, approved)

                # Phase 6: Merging
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.MERGING)
                await self._merge(session, approved)

                await self._update_run_status(session, PipelineStatus.COMPLETED)

        except asyncio.CancelledError:
            logger.info("Pipeline %s cancelled", self.run_id)
            async with self.session_factory() as session:
                await self._update_run_status(session, PipelineStatus.CANCELLED)
        except Exception as e:
            logger.exception("Pipeline %s failed: %s", self.run_id, e)
            try:
                async with self.session_factory() as session:
                    result = await session.execute(
                        select(PipelineRun).where(PipelineRun.id == self.run_id),
                    )
                    run = result.scalar_one()
                    run.status = PipelineStatus.FAILED.value
                    run.error_message = str(e)
                    run.completed_at = datetime.now(timezone.utc)
                    await session.commit()
            except Exception:
                logger.exception("Failed to update run status after error")
            await self._broadcast(EventType.ERROR, {"message": str(e)})

    async def _plan(self, session: AsyncSession) -> list[PipelineTask]:
        planner = PlannerAgent(self.provider, self.model, self.run_id)
        task_defs = await planner.plan(self.goal, self.project_context)

        # Validate and correct planner-suggested file paths against real project files
        if self.project_path:
            try:
                analysis = analyze_project(self.project_path)
                task_defs = correct_file_paths(task_defs, analysis["all_files"])
            except Exception as e:
                logger.warning("File path correction failed: %s", e)

        db_tasks = []
        for task_def in task_defs:
            task = PipelineTask(
                run_id=self.run_id,
                title=task_def["title"],
                description=task_def["description"],
                specialty_tags=task_def.get("specialty_tags", []),
                file_paths=task_def.get("file_paths", []),
            )
            session.add(task)
            db_tasks.append(task)

        # Update run with total tasks
        result = await session.execute(select(PipelineRun).where(PipelineRun.id == self.run_id))
        run = result.scalar_one()
        run.total_tasks = len(db_tasks)
        await session.commit()

        for task in db_tasks:
            await self._broadcast(EventType.TASK_CREATED, {
                "task_id": task.id, "title": task.title,
                "specialty_tags": task.specialty_tags,
            })

        return db_tasks

    async def _assign_tasks(
        self, session: AsyncSession, tasks: list[PipelineTask],
    ) -> tuple[dict[str, tuple[PipelineTask, DeveloperConfig]], list[PipelineTask]]:
        """Assign tasks to available developers.

        Returns (assignments, unassigned_tasks).
        """
        assignments: dict[str, tuple[PipelineTask, DeveloperConfig]] = {}
        unassigned: list[PipelineTask] = []

        for task in tasks:
            await self._check_pause()
            dev_id = await self.assigner.assign(task.specialty_tags or [], task.title)
            if dev_id is None:
                unassigned.append(task)
                continue

            dev_config = next((d for d in self.developers if d.id == dev_id), None)
            if dev_config is None:
                unassigned.append(task)
                continue

            self.assigner.mark_busy(dev_id, task.id)
            task.assigned_to = dev_config.name
            task.status = TaskStatus.ASSIGNED.value
            assignments[task.id] = (task, dev_config)

            await self._broadcast(EventType.TASK_ASSIGNED, {
                "task_id": task.id, "developer": dev_config.name,
                "developer_emoji": dev_config.emoji,
            })

        await session.commit()
        return assignments, unassigned

    async def _develop(self, session: AsyncSession,
                       assignments: dict[str, tuple[PipelineTask, DeveloperConfig]]) -> dict[str, dict[str, str]]:
        code_outputs: dict[str, dict[str, str]] = {}

        async def develop_task(task_id: str, task: PipelineTask, dev: DeveloperConfig) -> None:
            await self._check_pause()
            task.status = TaskStatus.IN_PROGRESS.value
            await self._broadcast(EventType.TASK_UPDATED, {
                "task_id": task_id, "status": TaskStatus.IN_PROGRESS.value,
            })

            agent = DeveloperAgent(
                self.provider, self.model, self.run_id,
                name=dev.name, specialty=dev.specialty,
                custom_instructions=dev.custom_prompt,
                detected_stack=self.detected_stack,
            )
            # Read only the files this task needs to modify
            task_files: dict[str, str] = {}
            if self.project_path and task.file_paths:
                task_files = read_task_files(self.project_path, task.file_paths)
                logger.info("Task '%s' - read %d/%d files: %s",
                            task.title, len(task_files), len(task.file_paths),
                            list(task_files.keys()))

            files = await agent.develop(
                task.title, task.description,
                self.project_context, task_files,
            )
            code_outputs[task_id] = files
            task.code_output = str(files)
            self.assigner.mark_idle(dev.id)

            await self._broadcast(EventType.CODE_GENERATED, {
                "agent": dev.name,
                "files": list(files.keys()),
                "contents": files,
            })

        coros = [
            develop_task(tid, task, dev)
            for tid, (task, dev) in assignments.items()
        ]
        await asyncio.gather(*coros, return_exceptions=True)
        await session.commit()
        return code_outputs

    async def _review(self, session: AsyncSession,
                      code_outputs: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
        approved: dict[str, dict[str, str]] = {}
        reviewer = ReviewerAgent(self.provider, self.model, self.run_id)

        for task_id, files in code_outputs.items():
            result = await session.execute(select(PipelineTask).where(PipelineTask.id == task_id))
            task = result.scalar_one()
            task.status = TaskStatus.IN_REVIEW.value
            await session.commit()
            await self._broadcast(EventType.TASK_UPDATED, {
                "task_id": task_id, "status": TaskStatus.IN_REVIEW.value,
            })

            for round_num in range(MAX_REVIEW_ROUNDS):
                await self._check_pause()
                review = await reviewer.review(task.title, files)
                task.review_notes = str(review.get("comments", []))

                if review.get("approved", False):
                    approved[task_id] = files
                    break

                if round_num < MAX_REVIEW_ROUNDS - 1:
                    task.status = TaskStatus.REVIEW_REJECTED.value
                    await session.commit()
                    await self._broadcast(EventType.TASK_UPDATED, {
                        "task_id": task_id, "status": TaskStatus.REVIEW_REJECTED.value,
                    })
                    # Re-develop with review feedback
                    dev_name = task.assigned_to or "Developer"
                    agent = DeveloperAgent(
                        self.provider, self.model, self.run_id, name=dev_name,
                    )
                    feedback = "\n".join(
                        c.get("message", "") for c in review.get("comments", [])
                    )
                    files = await agent.develop(
                        task.title,
                        f"{task.description}\n\nReview feedback:\n{feedback}",
                        self.project_context,
                    )
                    code_outputs[task_id] = files
                    task.code_output = str(files)
            else:
                # Max rounds reached, accept anyway
                approved[task_id] = files

            await session.commit()

        return approved

    async def _test(self, session: AsyncSession, approved: dict[str, dict[str, str]]) -> None:
        tester = TesterAgent(self.provider, self.model, self.run_id)

        for task_id, files in approved.items():
            await self._check_pause()
            result_row = await session.execute(select(PipelineTask).where(PipelineTask.id == task_id))
            task = result_row.scalar_one()
            task.status = TaskStatus.TESTING.value
            await session.commit()
            await self._broadcast(EventType.TASK_UPDATED, {
                "task_id": task_id, "status": TaskStatus.TESTING.value,
            })

            try:
                test_result = await asyncio.wait_for(
                    tester.test(task.title, files), timeout=300,
                )
                task.test_results = str(test_result)
            except asyncio.TimeoutError:
                logger.warning("Test timed out for task %s", task_id)
                task.test_results = "Test timed out"
            except Exception as e:
                logger.warning("Test failed for task %s: %s", task_id, e)
                task.test_results = f"Test error: {e}"

            task.status = TaskStatus.COMPLETED.value
            await session.commit()

            # Increment completed count
            run_result = await session.execute(select(PipelineRun).where(PipelineRun.id == self.run_id))
            run = run_result.scalar_one()
            run.completed_tasks += 1
            await session.commit()

            await self._broadcast(EventType.TASK_UPDATED, {
                "task_id": task_id, "status": TaskStatus.COMPLETED.value,
            })

    async def _merge(self, session: AsyncSession, approved: dict[str, dict[str, str]]) -> None:
        merged, conflicts = merge_task_outputs(approved)

        if conflicts:
            await self._broadcast(EventType.LOG, {
                "message": f"Conflicts detected in {len(conflicts)} files: {', '.join(conflicts)}",
            })

        await self._broadcast(EventType.LOG, {
            "message": f"Merged {len(merged)} files from {len(approved)} tasks",
        })

        for filepath in list(merged.keys()):
            await self._broadcast(EventType.CODE_GENERATED, {
                "agent": "merger",
                "files": [filepath],
                "contents": {filepath: merged[filepath]},
            })

        # Determine where to write files and how to handle git
        target_path = self.project_path or ""
        is_existing_repo = False

        if target_path:
            try:
                is_existing_repo = await is_git_repo(target_path)
            except Exception:
                pass

        if is_existing_repo:
            # Working with a cloned repo - create branch, write files, commit, push
            try:
                branch_name = f"ai-dev-team/{self.run_id[:8]}"
                await create_branch(target_path, branch_name)
                await self._broadcast(EventType.LOG, {
                    "message": f"Created branch '{branch_name}'",
                })

                # Write merged files directly into the repo
                src_path = Path(target_path).expanduser().resolve()
                for filepath, content in merged.items():
                    target = src_path / filepath
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content)

                await self._broadcast(EventType.LOG, {
                    "message": f"Applied {len(merged)} files to {target_path}",
                })

                # Commit
                commit_hash = await commit_files(target_path, f"AI Dev Team: {self.goal}")
                await self._broadcast(EventType.LOG, {
                    "message": f"Committed ({commit_hash[:8]})",
                })

                # Push
                try:
                    await push_branch(target_path, branch_name)
                    await self._broadcast(EventType.LOG, {
                        "message": f"Pushed branch '{branch_name}' to origin",
                    })
                except Exception as e:
                    logger.warning("Git push failed (non-fatal): %s", e)
                    await self._broadcast(EventType.LOG, {
                        "message": f"Push skipped (commit is local): {e}",
                    })

            except Exception as e:
                logger.exception("Git operations failed: %s", e)
                await self._broadcast(EventType.LOG, {
                    "message": f"Git operations failed: {e}",
                })
        else:
            # No existing repo - write to workspace and init a fresh repo
            written = write_files(self.run_id, merged)

            # Also write back to source directory if provided
            if target_path:
                try:
                    src_path = Path(target_path).expanduser().resolve()
                    for filepath, content in merged.items():
                        t = src_path / filepath
                        t.parent.mkdir(parents=True, exist_ok=True)
                        t.write_text(content)
                except Exception as e:
                    logger.warning("Write-back failed: %s", e)

            try:
                ws_path = get_workspace_path(self.run_id)
                await init_repo(ws_path)
                branch_name = f"ai-dev-team/{self.run_id[:8]}"
                await create_branch(ws_path, branch_name)
                commit_hash = await commit_files(ws_path, f"AI Dev Team: {self.goal}")
                await self._broadcast(EventType.LOG, {
                    "message": f"Committed to workspace branch '{branch_name}' ({commit_hash[:8]})",
                })
            except Exception as e:
                logger.warning("Git commit failed (non-fatal): %s", e)
                await self._broadcast(EventType.LOG, {
                    "message": f"Git commit skipped: {e}",
                })
