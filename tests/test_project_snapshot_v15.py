from pathlib import Path

import pytest

from app.repair.project_snapshot import (
    FileSnapshot,
    ProjectSnapshot,
    ProjectSnapshotter,
    create_project_snapshot,
)


def test_snapshot_captures_files(tmp_path):
    (tmp_path / "app.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    snapshot = ProjectSnapshotter().create(tmp_path)

    assert isinstance(snapshot, ProjectSnapshot)
    assert snapshot.file_count == 1
    assert snapshot.files[0].path == "app.py"
    assert snapshot.files[0].size > 0
    assert len(snapshot.files[0].sha256) == 64


def test_snapshot_fingerprint_is_stable(tmp_path):
    file = tmp_path / "app.py"
    file.write_text("print('hello')", encoding="utf-8")

    snapshot_one = ProjectSnapshotter().create(tmp_path)
    snapshot_two = ProjectSnapshotter().create(tmp_path)

    assert snapshot_one.fingerprint == snapshot_two.fingerprint


def test_snapshot_changes_when_file_changes(tmp_path):
    file = tmp_path / "app.py"

    file.write_text("print('hello')", encoding="utf-8")
    before = ProjectSnapshotter().create(tmp_path)

    file.write_text("print('changed')", encoding="utf-8")
    after = ProjectSnapshotter().create(tmp_path)

    assert before.fingerprint != after.fingerprint


def test_snapshot_ignores_generated_directories(tmp_path):
    (tmp_path / "app.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()

    (node_modules / "package.js").write_text(
        "generated",
        encoding="utf-8",
    )

    snapshot = ProjectSnapshotter().create(tmp_path)

    paths = [item.path for item in snapshot.files]

    assert "app.py" in paths
    assert not any(path.startswith("node_modules") for path in paths)


def test_snapshot_supports_nested_files(tmp_path):
    source = tmp_path / "src"
    source.mkdir()

    (source / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    snapshot = ProjectSnapshotter().create(tmp_path)

    assert snapshot.file_count == 1
    assert snapshot.files[0].path == str(
        Path("src") / "main.py"
    )


def test_snapshot_total_size(tmp_path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"

    first.write_text("abc", encoding="utf-8")
    second.write_text("12345", encoding="utf-8")

    snapshot = ProjectSnapshotter().create(tmp_path)

    assert snapshot.total_size == 8


def test_snapshot_returns_serializable_dict(tmp_path):
    (tmp_path / "app.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    result = create_project_snapshot(tmp_path)

    assert isinstance(result, dict)
    assert result["file_count"] == 1
    assert isinstance(result["files"], list)
    assert len(result["fingerprint"]) == 64


def test_snapshot_rejects_missing_root(tmp_path):
    snapshotter = ProjectSnapshotter()

    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        snapshotter.create(missing)


def test_snapshot_rejects_file_as_root(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("test", encoding="utf-8")

    snapshotter = ProjectSnapshotter()

    with pytest.raises(NotADirectoryError):
        snapshotter.create(file)


def test_snapshot_custom_ignored_directory(tmp_path):
    ignored = tmp_path / "custom_generated"
    ignored.mkdir()

    (ignored / "generated.txt").write_text(
        "generated",
        encoding="utf-8",
    )

    snapshotter = ProjectSnapshotter(
        ignored_directories={"custom_generated"}
    )

    snapshot = snapshotter.create(tmp_path)

    assert snapshot.file_count == 0


def test_snapshot_file_objects_are_serializable(tmp_path):
    (tmp_path / "test.txt").write_text(
        "FixPilot",
        encoding="utf-8",
    )

    snapshot = ProjectSnapshotter().create(tmp_path)

    assert isinstance(snapshot.files[0], FileSnapshot)
    assert isinstance(snapshot.files[0].as_dict(), dict)
    assert snapshot.files[0].as_dict()["path"] == "test.txt"