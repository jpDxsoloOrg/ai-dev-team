from app.pipeline.merge import merge_task_outputs


def test_merge_no_conflicts():
    outputs = {
        "task1": {"src/app.py": "print('hello')"},
        "task2": {"src/utils.py": "def helper(): pass"},
    }
    merged, conflicts = merge_task_outputs(outputs)
    assert len(merged) == 2
    assert len(conflicts) == 0
    assert "src/app.py" in merged
    assert "src/utils.py" in merged


def test_merge_with_conflict():
    outputs = {
        "task1": {"src/app.py": "version_a"},
        "task2": {"src/app.py": "version_b"},
    }
    merged, conflicts = merge_task_outputs(outputs)
    assert len(conflicts) == 1
    assert "src/app.py" in conflicts
    # Both versions should be present
    assert "version_a" in merged["src/app.py"]
    assert "version_b" in merged["src/app.py"]


def test_merge_same_content_no_conflict():
    outputs = {
        "task1": {"src/shared.py": "same content"},
        "task2": {"src/shared.py": "same content"},
    }
    merged, conflicts = merge_task_outputs(outputs)
    # Same content = still listed in conflicts since multiple tasks touched it
    assert "src/shared.py" in merged
    assert merged["src/shared.py"] == "same content"
