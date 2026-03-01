import logging

logger = logging.getLogger(__name__)

CONFLICT_MARKER = "<<<< CONFLICT: multiple tasks modified this file >>>>"


def merge_task_outputs(task_outputs: dict[str, dict[str, str]]) -> tuple[dict[str, str], list[str]]:
    """Merge file outputs from multiple tasks.

    Returns (merged_files, conflicts) where conflicts is a list of file paths
    that were modified by multiple tasks.
    """
    merged: dict[str, str] = {}
    file_sources: dict[str, list[str]] = {}  # filepath -> list of task_ids

    for task_id, files in task_outputs.items():
        for filepath, content in files.items():
            if filepath not in file_sources:
                file_sources[filepath] = []
            file_sources[filepath].append(task_id)

            if filepath in merged and merged[filepath] != content:
                # Conflict: append with markers
                merged[filepath] = (
                    merged[filepath]
                    + f"\n\n{CONFLICT_MARKER}\n"
                    + f"# From task: {task_id}\n"
                    + content
                )
            else:
                merged[filepath] = content

    conflicts = [fp for fp, sources in file_sources.items() if len(sources) > 1]
    if conflicts:
        logger.warning("File conflicts detected in: %s", conflicts)

    return merged, conflicts
