import os
from pathlib import Path


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


def analyze_project(project_path: str) -> dict:
    path = Path(project_path).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {path}")

    detected_stack: list[str] = []
    key_file_contents: dict[str, str] = {}
    all_files: list[str] = []

    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and common large dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build')]

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
        "key_files": key_file_contents,
        "summary": " | ".join(summary_parts),
    }
