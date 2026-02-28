# AI Dev Team Pipeline

Orchestrate multiple AI developer agents to collaboratively build software. Describe a goal, and the system plans tasks, assigns them to specialty-matched developer agents, reviews code, tests it, and merges results.

## Features

- **Multi-provider LLM support**: Ollama (local), OpenAI, Anthropic/Claude
- **Project modes**: Start from scratch or open an existing project (local path or GitHub URL)
- **Configurable developer agents**: Name, emoji, color, specialty prompt. Toggle on/off
- **Intelligent task assignment**: 3-tier specialty matching (keyword heuristic, idle timeout, LLM scoring)
- **Full pipeline**: Planning -> Assignment -> Parallel Development -> Code Review -> Testing -> Merge
- **Real-time UI**: WebSocket-driven event feed, task board, code viewer
- **Export**: Download ZIP, create git repo, export transcript

## Tech Stack

- **Frontend**: React + Vite + TypeScript
- **Backend**: Python FastAPI (async, WebSocket)
- **Storage**: SQLite (pipeline history) + JSON files (developer configs)

## Getting Started

See [docs/plans/implementation-plan.md](docs/plans/implementation-plan.md) for the full implementation plan.

## License

MIT
