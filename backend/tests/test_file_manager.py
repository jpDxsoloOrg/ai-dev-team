import os
import tempfile

import pytest

from app.services import file_manager


@pytest.fixture(autouse=True)
def temp_workspace(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.services.file_manager.settings.workspace_dir", tmpdir)
        yield tmpdir


def test_write_and_read():
    file_manager.write_file("test-run", "src/app.py", "print('hi')")
    content = file_manager.read_file("test-run", "src/app.py")
    assert content == "print('hi')"


def test_list_files():
    file_manager.write_file("test-run", "a.py", "a")
    file_manager.write_file("test-run", "b/c.py", "c")
    files = file_manager.list_files("test-run")
    assert "a.py" in files
    assert os.path.join("b", "c.py") in files


def test_write_files():
    written = file_manager.write_files("test-run", {
        "x.py": "x",
        "y/z.py": "z",
    })
    assert len(written) == 2


def test_read_nonexistent():
    with pytest.raises(FileNotFoundError):
        file_manager.read_file("test-run", "nonexistent.py")
