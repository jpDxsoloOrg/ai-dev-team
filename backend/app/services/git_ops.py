import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


async def _run(cmd: list[str], cwd: str | None = None) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")
    return stdout.decode().strip()


async def clone_repo(url: str, dest: str) -> str:
    dest_path = Path(dest).expanduser().resolve()
    dest_path.mkdir(parents=True, exist_ok=True)

    repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = str(dest_path / repo_name)

    if os.path.exists(clone_path):
        logger.info("Repo already exists at %s, pulling latest", clone_path)
        await _run(["git", "pull"], cwd=clone_path)
        return clone_path

    await _run(["git", "clone", url, clone_path])
    return clone_path


async def create_branch(repo_path: str, branch_name: str) -> None:
    await _run(["git", "checkout", "-b", branch_name], cwd=repo_path)


async def commit_files(repo_path: str, message: str) -> str:
    await _run(["git", "add", "-A"], cwd=repo_path)
    await _run(["git", "commit", "-m", message], cwd=repo_path)
    result = await _run(["git", "rev-parse", "HEAD"], cwd=repo_path)
    return result


async def push_branch(repo_path: str, branch_name: str) -> None:
    await _run(["git", "push", "-u", "origin", branch_name], cwd=repo_path)


async def init_repo(path: str) -> None:
    await _run(["git", "init"], cwd=path)


async def is_git_repo(path: str) -> bool:
    """Check if a directory is already a git repository."""
    try:
        await _run(["git", "rev-parse", "--git-dir"], cwd=path)
        return True
    except RuntimeError:
        return False
