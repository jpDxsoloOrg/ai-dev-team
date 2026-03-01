# AI Dev Team Pipeline

## Project Structure
- `backend/` - Python FastAPI async backend
- `frontend/` - React + Vite + TypeScript frontend
- `.github/workflows/ci.yml` - CI pipeline

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy async + aiosqlite, WebSockets
- **Frontend**: React 19, TypeScript, Vite
- **LLM Providers**: Ollama (local), OpenAI, Anthropic

## Development

### Backend
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload  # port 8000
python -m pytest tests/ -v     # run tests
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # port 5173, proxies /api and /ws to backend
npm run lint  # lint
npx tsc -b --noEmit  # typecheck
```

## Architecture

### Backend Modules
- `app/models/` - SQLAlchemy ORM + Pydantic schemas + enums
- `app/providers/` - Abstract LLM provider with Ollama/OpenAI/Anthropic implementations
- `app/agents/` - Planner, Developer, Reviewer, Tester agents with prompt templates
- `app/pipeline/` - Orchestrator, task assigner (3-tier), merge, state management
- `app/routes/` - REST API routes (pipeline, developers, providers, settings, projects, export, history)
- `app/ws/` - WebSocket manager + event system (12 event types)
- `app/services/` - Developer store, key store, file manager, project analyzer, git ops

### Frontend Modules
- `src/components/layout/` - AppLayout, Header, Sidebar
- `src/components/pipeline/` - Controls, ProgressBar, TaskBoard, TaskCard, EventFeed
- `src/components/developers/` - DeveloperCards, DeveloperCard, AddDevModal
- `src/components/code/` - CodeViewer, FileTree
- `src/components/settings/` - ProviderSelect, ApiKeyManager, ProjectLoader
- `src/components/export/` - ExportPanel
- `src/contexts/` - PipelineContext (WS events -> state), SettingsContext (provider/model/keys)
- `src/hooks/` - useWebSocket (reconnect), useDevelopers (CRUD)
- `src/services/api.ts` - Typed REST client

## Code Style
- Python: async/await, type hints, Pydantic models
- TypeScript: strict mode, no `any`, functional components with hooks
- Path alias: `@/` maps to `frontend/src/`
