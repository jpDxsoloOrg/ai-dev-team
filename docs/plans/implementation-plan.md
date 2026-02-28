# AI Dev Team Pipeline - Implementation Plan

## Context

Build a web app that orchestrates multiple AI "developer agents" to collaboratively build software. The user describes a goal, and the system plans tasks, assigns them to specialty-matched developer agents, reviews code, tests it, and merges results. The user attached a prototype (single-file FastAPI + CDN React) that demonstrates the concept but needs a proper production architecture.

**Repo**: `jpDxsoloOrg/ai-dev-team`
**Stack**: Python FastAPI backend + React/Vite/TypeScript frontend
**Storage**: SQLite (pipeline history) + JSON files (developer configs, API keys)

---

## Repository Structure

```
ai-dev-team/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app, CORS, lifespan
│   │   ├── config.py                   # pydantic-settings from .env
│   │   ├── models/
│   │   │   ├── database.py             # Async SQLAlchemy + aiosqlite
│   │   │   ├── pipeline.py             # PipelineRun, PipelineTask ORM
│   │   │   ├── schemas.py              # Pydantic request/response schemas
│   │   │   └── enums.py                # Status enums
│   │   ├── providers/
│   │   │   ├── base.py                 # Abstract LLMProvider interface
│   │   │   ├── ollama.py               # Local Ollama via httpx
│   │   │   ├── openai.py               # OpenAI SDK async client
│   │   │   ├── anthropic.py            # Anthropic SDK async client
│   │   │   └── registry.py             # Provider registry + model listing
│   │   ├── agents/
│   │   │   ├── base.py                 # BaseAgent with LLM call + event broadcast
│   │   │   ├── planner.py              # Breaks goal into tasks
│   │   │   ├── developer.py            # Writes code for assigned task
│   │   │   ├── reviewer.py             # Reviews code quality
│   │   │   ├── tester.py               # Validates code
│   │   │   └── prompts.py              # All system prompt templates
│   │   ├── pipeline/
│   │   │   ├── orchestrator.py          # Main engine: plan->assign->dev->review->test->merge
│   │   │   ├── task_assigner.py         # 3-tier specialty matching
│   │   │   ├── state.py                 # In-memory pipeline state + pause/resume
│   │   │   └── merge.py                 # File assembly + conflict handling
│   │   ├── routes/
│   │   │   ├── pipeline.py              # start/pause/resume/stop
│   │   │   ├── developers.py            # CRUD for developer agents
│   │   │   ├── providers.py             # List providers + models
│   │   │   ├── projects.py              # Load local/GitHub projects
│   │   │   ├── settings.py              # API key management
│   │   │   ├── export.py                # zip/transcript/git export
│   │   │   └── history.py               # Past pipeline runs
│   │   ├── ws/
│   │   │   ├── manager.py               # WebSocket connection manager
│   │   │   └── events.py                # Event types + broadcast helpers
│   │   └── services/
│   │       ├── git_ops.py               # Clone, branch, commit
│   │       ├── project_analyzer.py      # Scan project, detect stack
│   │       ├── file_manager.py          # Workspace read/write
│   │       └── key_store.py             # API key persistence
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── types/
│   │   │   ├── index.ts                # All TS interfaces
│   │   │   └── events.ts               # WebSocket event union type
│   │   ├── contexts/
│   │   │   ├── PipelineContext.tsx       # Pipeline state from WebSocket
│   │   │   └── SettingsContext.tsx       # Provider, model, keys
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts          # WS connection + reconnect
│   │   │   ├── usePipeline.ts           # Pipeline control actions
│   │   │   └── useDevelopers.ts         # Developer CRUD
│   │   ├── services/
│   │   │   └── api.ts                   # Typed REST client
│   │   ├── components/
│   │   │   ├── layout/                  # AppLayout, Header, Sidebar
│   │   │   ├── pipeline/               # EventFeed, TaskBoard, TaskCard, ProgressBar, Controls
│   │   │   ├── developers/             # DeveloperCards, DeveloperCard, AddDevModal, Toggle
│   │   │   ├── code/                   # CodeViewer, FileTree
│   │   │   ├── settings/              # ApiKeyManager, ProviderSelect, ProjectLoader
│   │   │   └── export/                # ExportPanel
│   │   └── utils/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .gitignore
├── README.md
└── CLAUDE.md
```

---

## Implementation Tasks (18 GitHub Issues)

### Issue 1: Repository Initialization and Project Scaffolding
- Init git repo, create monorepo structure
- Backend: `pyproject.toml`, FastAPI app with `/health` endpoint, CORS config, `pydantic-settings` config
- Frontend: Vite + React + TypeScript scaffold, proxy config for `/api` and `/ws`
- Root: `docker-compose.yml`, `.gitignore`, `README.md`, `CLAUDE.md`
- **Acceptance**: Backend serves health endpoint, frontend calls it successfully

### Issue 2: Backend Data Models and Database Layer
- `enums.py`: PipelineStatus, TaskStatus, AgentRole enums
- `database.py`: Async SQLAlchemy engine + aiosqlite, auto-create tables on startup
- `pipeline.py`: PipelineRun and PipelineTask ORM models (with UUID PKs, status, timestamps, JSON fields)
- `schemas.py`: Pydantic schemas for all requests/responses (DeveloperConfig, PipelineStartRequest, etc.)
- **Acceptance**: Tables auto-create, schemas validate correctly

### Issue 3: LLM Provider Abstraction Layer
- `base.py`: Abstract `LLMProvider` with `generate()`, `list_models()`, `is_available()`
- `ollama.py`: httpx calls to `/api/chat` and `/api/tags`
- `openai.py`: OpenAI SDK async client
- `anthropic.py`: Anthropic SDK async client, hardcoded model list
- `registry.py`: Singleton provider registry
- All providers normalize to same `messages` format; provider handles conversion
- **Acceptance**: Each provider returns string responses, registry resolves correctly

### Issue 4: WebSocket Manager and Event System
- Event types: pipeline_status, task_created, task_assigned, task_updated, agent_thinking, agent_output, code_generated, review_result, test_result, error, log
- `WebSocketManager`: connect/disconnect/broadcast with dead socket cleanup
- WebSocket endpoint in `main.py`
- **Acceptance**: Browser connects, receives broadcast events, disconnection handled gracefully

### Issue 5: Agent System - Base Agent and Prompts
- `BaseAgent`: Builds messages, calls provider, broadcasts thinking/output events
- `prompts.py`: System prompt templates for planner, developer (with `{name}`, `{specialty}`), reviewer, tester
- `PlannerAgent`: Parses JSON task list from LLM response
- `DeveloperAgent`: Parses `filepath:` code blocks into file-path-to-content mappings
- `ReviewerAgent`: Parses JSON review result (approved/rejected + comments)
- `TesterAgent`: Generates/evaluates tests, returns pass/fail
- **Acceptance**: Each agent works with mock provider, returns structured output

### Issue 6: Developer Agent Config Persistence and CRUD API
- `developers.json`: Ships with 4 default developers (Ada, Linus, Grace, Alan)
- `developer_store.py`: Load, list, create, update, delete, duplicate, toggle, save to JSON
- REST routes: GET/POST/PUT/DELETE `/api/developers`, `/api/developers/{id}/duplicate`, `/api/developers/{id}/toggle`
- **Acceptance**: CRUD persists to disk, survives server restart

### Issue 7: Task Assignment Engine (3-Tier Specialty Matching)
- **Tier 1 - Keyword heuristic**: Score task specialty_tags against developer specialty keywords, assign if score > threshold
- **Tier 2 - Idle timeout**: If no keyword match, wait. When dev idle > configurable timeout, they become eligible for any task
- **Tier 3 - LLM scoring**: Ask LLM to score multiple eligible devs, pick highest
- Track developer idle_since timestamps
- **Acceptance**: Unit tests cover all three tiers, timeout correctly promotes devs

### Issue 8: Pipeline Orchestrator Engine
- `orchestrator.py`: Main `run()` method driving phases: Planning -> Assigning -> Developing (parallel via asyncio.gather) -> Reviewing (loop back on rejection, max rounds) -> Testing -> Merging
- `state.py`: Holds current orchestrator instance, pause via asyncio.Event, stop via task cancellation
- Re-assign freed developers to remaining tasks after each completion
- **Acceptance**: Full pipeline with mock provider goes through all phases, events broadcast at each transition

### Issue 9: REST API Routes (Pipeline, Providers, History, Settings)
- Pipeline: POST start/pause/resume/stop, GET status
- Providers: GET list with availability, GET models per provider
- History: GET past runs (paginated), GET single run with tasks
- Settings: PUT/DELETE/GET API keys (stored via key_store, never returned in full)
- Register all routers under `/api` prefix
- **Acceptance**: All endpoints return proper JSON, pipeline start creates background task

### Issue 10: Frontend Scaffolding, Types, and State Management
- `types/index.ts`: DeveloperConfig, PipelineTask, PipelineRun, ProviderInfo interfaces
- `types/events.ts`: Discriminated union for WebSocket events
- `services/api.ts`: Typed REST client for all endpoints
- `hooks/useWebSocket.ts`: Auto-reconnect with exponential backoff, capped event buffer
- `contexts/PipelineContext.tsx`: Processes WS events into pipeline state, exposes control actions
- `contexts/SettingsContext.tsx`: Provider/model selection, API key status
- **Acceptance**: Types compile, contexts provide correct state, WS hook connects

### Issue 11: Frontend Layout and Navigation Shell
- `AppLayout.tsx`: CSS Grid - 320px sidebar + flexible main area
- `Header.tsx`: Title, connection status dot, pipeline status badge
- `Sidebar.tsx`: Collapsible sections for Project, Provider, Team, Settings
- Dark theme CSS custom properties in `index.css`
- **Acceptance**: Layout renders, sections collapse/expand

### Issue 12: Pipeline UI Components
- `PipelineControls.tsx`: Start (opens goal input), Pause/Resume toggle, Stop with confirm
- `ProgressBar.tsx`: Segmented bar with task status colors + phase label
- `TaskBoard.tsx`: Kanban columns (Pending | In Progress | In Review | Completed | Failed)
- `TaskCard.tsx`: Title, assigned dev, specialty tags, expandable code/review details
- `EventFeed.tsx`: Scrolling log with agent emoji, timestamps, auto-scroll with scroll-lock detection
- **Acceptance**: Components render with mock data, TaskBoard moves cards on events

### Issue 13: Developer Agent Management UI
- `DeveloperCards.tsx`: Grid with "Add Developer" button
- `DeveloperCard.tsx`: Emoji, name, specialty, color border, status indicator, toggle, context menu (edit/duplicate/delete)
- `AddDevModal.tsx`: Modal form for create/edit (name, emoji, color picker, specialty, custom prompt)
- `useDevelopers` hook: CRUD operations calling API and updating local state
- **Acceptance**: Full CRUD works, persists, updates in real-time during pipeline runs

### Issue 14: Project Loading and Analysis
- Backend: `POST /api/projects/load` (local path or GitHub URL), `project_analyzer.py` (scan dir, detect stack, read key files), `git_ops.py` (clone, branch, commit via asyncio subprocess)
- Frontend: `ProjectLoader.tsx` - radio buttons (New/Local/GitHub), path/URL input, load button, shows analysis result
- **Acceptance**: Load local dir, clone GitHub repo, project context passed to planner

### Issue 15: Code Viewer and File Tree
- `FileTree.tsx`: Tree view of generated files, file-type icons, new/modified badges
- `CodeViewer.tsx`: Syntax highlighting (prism-react-renderer), line numbers, copy button, file path header
- Data flow: code_generated events accumulate files in PipelineContext
- **Acceptance**: Correct highlighting, file navigation works, copy button works

### Issue 16: Export Functionality
- Backend: GET `/api/export/{run_id}/zip` (streaming zip), GET `/api/export/{run_id}/transcript` (markdown), POST `/api/export/{run_id}/git` (commit to repo/branch)
- Frontend: `ExportPanel.tsx` - Download ZIP, Download Transcript, Push to Git buttons
- **Acceptance**: ZIP extracts correctly, transcript is readable, git push creates commit

### Issue 17: File Assembly and Workspace Management
- `file_manager.py`: Per-run workspace dir (`~/.ai-dev-team/workspaces/{run_id}/`), read/write/list files
- `merge.py`: Assemble approved task outputs, detect same-file conflicts, handle via section markers or reviewer reconciliation
- For existing projects: apply changes as overwrites/additions
- **Acceptance**: Multi-task merge works, conflicts detected, workspace clean

### Issue 18: Testing, CI, and Documentation
- Backend tests: conftest with fixtures, test providers/assigner/pipeline/routes
- Frontend tests: Vitest, test useWebSocket + PipelineContext
- CI: `.github/workflows/ci.yml` - lint + typecheck + test for both backend and frontend on PR
- Documentation: Complete README, CLAUDE.md, inline docstrings
- **Acceptance**: All tests pass, CI green, README sufficient for onboarding

---

## Dependency Graph

```
Issue 1 (Scaffold)
├── Issue 2 (Data Models)
│   ├── Issue 3 (LLM Providers)     ─┐
│   ├── Issue 4 (WebSocket)          │── can parallelize
│   └── Issue 6 (Developer CRUD)    ─┘
│       │
│       ├── Issue 5 (Agent System)  ← needs providers + WS
│       │   └── Issue 7 (Task Assigner)
│       │       └── Issue 8 (Orchestrator) ← core engine
│       │           └── Issue 17 (Merge/Workspace)
│       └── Issue 9 (REST Routes) ← needs all backend pieces
│
├── Issue 10 (Frontend Types/State/Hooks)
│   ├── Issue 11 (Layout Shell)
│   │   ├── Issue 12 (Pipeline UI)   ─┐
│   │   ├── Issue 13 (Dev Mgmt UI)    │── can parallelize
│   │   └── Issue 15 (Code Viewer)   ─┘
│   ├── Issue 14 (Project Loading)
│   └── Issue 16 (Export)
│
└── Issue 18 (Testing/CI/Docs) ← started early, completed last
```

## Execution Plan

1. Create GitHub repo `jpDxsoloOrg/ai-dev-team`
2. Implement Issue 1 (scaffolding), push initial commit
3. Create all 18 GitHub issues with labels and milestone
4. Work through issues in dependency order, creating branches per issue

## Verification

- Backend: `cd backend && uvicorn app.main:app --reload` on port 8000
- Frontend: `cd frontend && npm run dev` on port 5173 (proxies to backend)
- Full pipeline test: Select a provider/model, enter a goal, verify all phases complete with real-time UI updates
- Export: Download ZIP, verify files extract correctly
- Developer management: Add/edit/toggle/delete devs, verify persistence
