import logging
import os
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


STACK_INDICATORS = {
    "package.json": "Node.js",
    "tsconfig.json": "TypeScript",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
}

KEY_FILES = [
    "README.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    ".gitignore",
    "Dockerfile",
    "docker-compose.yml",
]

SKIP_DIRS = {
    "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
    ".next", ".cache", ".tox", "egg-info", "coverage",
}


def analyze_project(project_path: str) -> dict:
    path = Path(project_path).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {path}")

    detected_stack: list[str] = []
    key_file_contents: dict[str, str] = {}
    all_files: list[str] = []

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]

        rel_root = os.path.relpath(root, path)
        for f in files:
            rel_path = os.path.join(rel_root, f) if rel_root != '.' else f
            all_files.append(rel_path)

            if f in STACK_INDICATORS and STACK_INDICATORS[f] not in detected_stack:
                detected_stack.append(STACK_INDICATORS[f])

            if f in KEY_FILES:
                try:
                    full = os.path.join(root, f)
                    content = Path(full).read_text(errors='replace')[:5000]
                    key_file_contents[rel_path] = content
                except Exception:
                    pass

    summary_parts = [f"Stack: {', '.join(detected_stack) or 'Unknown'}"]
    summary_parts.append(f"Files: {len(all_files)}")
    if key_file_contents:
        summary_parts.append(f"Key files: {', '.join(key_file_contents.keys())}")

    return {
        "path": str(path),
        "detected_stack": detected_stack,
        "file_count": len(all_files),
        "all_files": all_files,
        "key_files": key_file_contents,
        "summary": " | ".join(summary_parts),
    }


# Source file extensions to include in deep context
SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".html", ".json",
    ".yaml", ".yml", ".toml", ".md", ".sql", ".sh", ".go", ".rs",
    ".java", ".rb", ".php", ".vue", ".svelte",
}

MAX_CONTEXT_BYTES = 50_000  # Cap total context to ~50KB


def analyze_for_context(project_path: str) -> str:
    """Build a compact project overview for the planner.

    Returns a filtered file tree (source files only) + key config contents.
    Keeps it small enough for local 14B models to process without confusion.
    """
    analysis = analyze_project(project_path)
    path = Path(project_path).expanduser().resolve()

    # Filter to source code files only — skip docs, configs, lock files, tests, etc.
    SKIP_EXTENSIONS = {".md", ".lock", ".log", ".txt", ".png", ".jpg", ".svg", ".ico", ".map", ".d.ts"}
    SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", ".gitignore", ".eslintrc", ".prettierrc"}

    source_files = []
    for f in analysis["all_files"]:
        name = os.path.basename(f)
        ext = os.path.splitext(f)[1].lower()
        if ext in SKIP_EXTENSIONS or name in SKIP_NAMES:
            continue
        if ext in SOURCE_EXTENSIONS or name in ("package.json", "tsconfig.json", "serverless.yml"):
            source_files.append(f)

    # Separate main source files from test files
    main_files = [f for f in source_files if "/__tests__/" not in f and "/test" not in f.lower() and ".test." not in f and ".spec." not in f]
    test_files = [f for f in source_files if f not in main_files]

    # Prioritize key files: types, models, components, routes, configs
    PRIORITY_KEYWORDS = {"types", "model", "interface", "schema", "component", "page", "route", "api", "service", "hook", "context", "App", "index", "config", "handler"}

    def file_priority(filepath: str) -> int:
        name = os.path.basename(filepath).split(".")[0]
        # Config files at top
        if name in ("package.json", "tsconfig.json", "serverless.yml"):
            return 0
        # Priority files next
        if any(kw.lower() in name.lower() or kw.lower() in filepath.lower() for kw in PRIORITY_KEYWORDS):
            return 1
        return 2

    main_files.sort(key=file_priority)

    parts: list[str] = []
    parts.append(f"Project: {path.name}")
    parts.append(f"Stack: {', '.join(analysis['detected_stack']) or 'Unknown'}")
    parts.append(f"Source files: {len(main_files)} (+ {len(test_files)} test files)")
    parts.append("")
    parts.append("File tree (use these EXACT paths when planning tasks):")

    # Show prioritized files (cap at 100)
    for f in main_files[:100]:
        parts.append(f"  {f}")
    if len(main_files) > 100:
        parts.append(f"  ... and {len(main_files) - 100} more source files")

    return "\n".join(parts)


def build_file_index(all_files: list[str]) -> dict[str, list[str]]:
    """Build a filename -> [full_paths] lookup for fast matching."""
    index: dict[str, list[str]] = defaultdict(list)
    for f in all_files:
        basename = os.path.basename(f)
        index[basename].append(f)
    return index


def find_best_match(suggested: str, all_files: list[str],
                    file_index: dict[str, list[str]] | None = None) -> str | None:
    """Find the best matching real file for a planner-suggested path.

    Priority: exact match → suffix match → filename with best directory overlap.
    """
    # Exact match
    if suggested in all_files:
        return suggested

    if file_index is None:
        file_index = build_file_index(all_files)

    basename = os.path.basename(suggested)
    candidates = file_index.get(basename, [])
    if not candidates:
        # Fallback: planner may invent a descriptive filename (e.g. player.ts)
        # when the real file is index.ts in the same directory
        suggested_dir = str(Path(suggested).parent)
        for index_name in ("index.ts", "index.tsx", "index.js", "index.jsx"):
            index_candidates = file_index.get(index_name, [])
            for ic in index_candidates:
                if str(Path(ic).parent).endswith(suggested_dir) or suggested_dir.endswith(str(Path(ic).parent)):
                    logger.info("Index fallback: '%s' -> '%s'", suggested, ic)
                    return ic
        return None

    # Suffix match: check if suggested path parts match the end of any candidate
    suggested_parts = Path(suggested).parts
    for candidate in candidates:
        candidate_parts = Path(candidate).parts
        if len(suggested_parts) <= len(candidate_parts):
            if candidate_parts[-len(suggested_parts):] == suggested_parts:
                return candidate

    # Directory overlap scoring: pick the candidate with most shared directory names
    suggested_dirs = set(Path(suggested).parent.parts)
    best_score = -1
    best_candidate = None
    for candidate in candidates:
        candidate_dirs = set(Path(candidate).parent.parts)
        score = len(suggested_dirs & candidate_dirs)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    # Only return if there's at least some directory overlap, or it's the only candidate
    if best_candidate and (best_score > 0 or len(candidates) == 1):
        return best_candidate

    return None


def correct_file_paths(task_defs: list[dict], all_files: list[str]) -> list[dict]:
    """Validate and correct planner-suggested file paths against real project files."""
    file_index = build_file_index(all_files)

    for task in task_defs:
        corrected = []
        for suggested in task.get("file_paths", []):
            match = find_best_match(suggested, all_files, file_index)
            if match:
                if match != suggested:
                    logger.info("Corrected file path: '%s' -> '%s'", suggested, match)
                corrected.append(match)
            else:
                logger.warning("No match for planner path '%s' — dropped", suggested)
        task["file_paths"] = corrected

    return task_defs


def read_task_files(project_path: str, file_paths: list[str]) -> dict[str, str]:
    """Read specific files from a project for a developer task.

    Returns {relative_path: content} for files that exist and are readable.
    Caps total size at MAX_CONTEXT_BYTES.
    """
    base = Path(project_path).expanduser().resolve()
    result: dict[str, str] = {}
    total = 0

    for rel_path in file_paths:
        full = base / rel_path
        if not full.is_file():
            logger.warning("File not found: '%s'", rel_path)
            continue

        try:
            content = full.read_text(errors="replace")
        except Exception:
            continue

        if len(content) > 15_000:
            content = content[:15_000] + "\n... (truncated)"

        if total + len(content) > MAX_CONTEXT_BYTES:
            break

        result[rel_path] = content
        total += len(content)

    return result
