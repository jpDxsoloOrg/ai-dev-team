import os
from pathlib import Path

from app.config import settings


def workspace_dir(run_id: str) -> Path:
    base = Path(settings.workspace_dir).expanduser().resolve()
    ws = base / run_id
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def write_file(run_id: str, filepath: str, content: str) -> str:
    ws = workspace_dir(run_id)
    target = ws / filepath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return str(target)


def read_file(run_id: str, filepath: str) -> str:
    ws = workspace_dir(run_id)
    target = ws / filepath
    if not target.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return target.read_text()


def list_files(run_id: str) -> list[str]:
    ws = workspace_dir(run_id)
    if not ws.exists():
        return []
    files: list[str] = []
    for root, _dirs, filenames in os.walk(ws):
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), ws)
            files.append(rel)
    return sorted(files)


def write_files(run_id: str, files: dict[str, str]) -> list[str]:
    written: list[str] = []
    for filepath, content in files.items():
        write_file(run_id, filepath, content)
        written.append(filepath)
    return written
