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


def get_workspace_path(run_id: str) -> str:
    return str(workspace_dir(run_id))


IGNORE_DIRS = {
    "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".git", ".next", ".cache", ".tox", "egg-info",
}


def copy_project_to_workspace(project_path: str, run_id: str) -> str:
    """Copy an existing project into the run workspace.

    Skips common non-source directories. Returns workspace path.
    """
    import shutil

    src = Path(project_path).expanduser().resolve()
    ws = workspace_dir(run_id)

    def _ignore(directory: str, contents: list[str]) -> set[str]:
        return {c for c in contents if c in IGNORE_DIRS or c.startswith(".")}

    if src.is_dir():
        shutil.copytree(src, ws, ignore=_ignore, dirs_exist_ok=True)

    return str(ws)
