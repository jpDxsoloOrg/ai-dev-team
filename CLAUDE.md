# AI Dev Team Pipeline

## Project Structure
- `backend/` - Python FastAPI async backend
- `frontend/` - React + Vite + TypeScript frontend
- `docs/plans/` - Implementation plans

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy async + aiosqlite, WebSockets
- **Frontend**: React 18, TypeScript, Vite
- **LLM Providers**: Ollama (local), OpenAI, Anthropic

## Development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # port 5173, proxies /api and /ws to backend
```

## Code Style
- Python: async/await, type hints, Pydantic models
- TypeScript: strict mode, no `any`, functional components with hooks
- Path alias: `@/` maps to `frontend/src/`
