import asyncio
import logging
from datetime import datetime, timezone

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
from app.services.file_manager import write_files
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
    ) -> None:
        self.run_id = run_id
        self.goal = goal
        self.provider = provider
        self.model = model
        self.developers = developers
        self.session_factory = session_factory
        self.pause_event = pause_event
        self.project_context = project_context
        self.assigner = TaskAssigner(developers, provider, model)

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

                # Phase 2: Assigning
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.ASSIGNING)
                assignments = await self._assign_tasks(session, tasks)

                # Phase 3: Developing (parallel)
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.DEVELOPING)
                code_outputs = await self._develop(session, assignments)

                # Phase 4: Reviewing
                await self._check_pause()
                await self._update_run_status(session, PipelineStatus.REVIEWING)
                approved = await self._review(session, code_outputs)

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

    async def _assign_tasks(self, session: AsyncSession,
                            tasks: list[PipelineTask]) -> dict[str, tuple[PipelineTask, DeveloperConfig]]:
        assignments: dict[str, tuple[PipelineTask, DeveloperConfig]] = {}

        for task in tasks:
            await self._check_pause()
            dev_id = await self.assigner.assign(task.specialty_tags or [], task.title)
            if dev_id is None:
                continue

            dev_config = next((d for d in self.developers if d.id == dev_id), None)
            if dev_config is None:
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
        return assignments

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
            )
            files = await agent.develop(task.title, task.description, self.project_context)
            code_outputs[task_id] = files
            task.code_output = str(files)
            self.assigner.mark_idle(dev.id)

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

            test_result = await tester.test(task.title, files)
            task.test_results = str(test_result)
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

        written = write_files(self.run_id, merged)

        await self._broadcast(EventType.LOG, {
            "message": f"Merged {len(written)} files from {len(approved)} tasks",
        })

        for filepath in written:
            await self._broadcast(EventType.CODE_GENERATED, {
                "agent": "merger",
                "files": [filepath],
            })
