"""Tests for the SQLite adapter."""

import tempfile
from pathlib import Path

import pytest

from actions.work_items import SQLiteAdapter, State, EmptyQueue


@pytest.fixture
def adapter():
    """Create a temporary SQLite adapter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        files_dir = Path(tmpdir) / "files"
        yield SQLiteAdapter(
            db_path=str(db_path),
            queue_name="test_queue",
            files_dir=str(files_dir),
        )


def test_seed_and_reserve(adapter):
    """Test seeding and reserving work items."""
    # Seed an item
    item_id = adapter.seed_input(
        payload={"key": "value"},
    )
    assert item_id

    # Reserve it
    reserved_id = adapter.reserve_input()
    assert reserved_id == item_id

    # No more items
    with pytest.raises(EmptyQueue):
        adapter.reserve_input()


def test_load_save_payload(adapter):
    """Test loading and saving payloads."""
    item_id = adapter.seed_input(payload={"initial": "data"})

    # Load
    payload = adapter.load_payload(item_id)
    assert payload == {"initial": "data"}

    # Save
    adapter.save_payload(item_id, {"updated": "data"})
    payload = adapter.load_payload(item_id)
    assert payload == {"updated": "data"}


def test_release_done(adapter):
    """Test releasing items as done."""
    item_id = adapter.seed_input()
    adapter.reserve_input()

    adapter.release_input(item_id, State.DONE)

    item = adapter.get_item(item_id)
    assert item["state"] == "DONE"


def test_release_failed(adapter):
    """Test releasing items as failed."""
    item_id = adapter.seed_input()
    adapter.reserve_input()

    adapter.release_input(
        item_id,
        State.FAILED,
        code="ERR001",
        message="Test error",
    )

    item = adapter.get_item(item_id)
    assert item["state"] == "FAILED"
    assert item["error_code"] == "ERR001"
    assert item["error_message"] == "Test error"


def test_create_output(adapter):
    """Test creating output items."""
    input_id = adapter.seed_input(payload={"input": "data"})
    adapter.reserve_input()

    output_id = adapter.create_output(input_id, payload={"output": "data"})

    assert output_id
    output_item = adapter.get_item(output_id)
    assert output_item["parent_id"] == input_id
    assert output_item["queue_name"] == "test_queue_output"
    assert output_item["payload"] == {"output": "data"}


def test_files(adapter):
    """Test file operations."""
    item_id = adapter.seed_input()

    # Add file
    content = b"Hello, World!"
    adapter.add_file(item_id, "test.txt", "test.txt", content)

    # List files
    files = adapter.list_files(item_id)
    assert "test.txt" in files

    # Get file
    retrieved = adapter.get_file(item_id, "test.txt")
    assert retrieved == content

    # Remove file
    adapter.remove_file(item_id, "test.txt")
    files = adapter.list_files(item_id)
    assert "test.txt" not in files


def test_list_items(adapter):
    """Test listing items."""
    # Seed multiple items
    adapter.seed_input(payload={"id": 1})
    adapter.seed_input(payload={"id": 2})
    adapter.seed_input(payload={"id": 3})

    # List all
    items = adapter.list_items()
    assert len(items) == 3

    # List by state
    pending = adapter.list_items(state=State.PENDING)
    assert len(pending) == 3

    # Reserve one
    adapter.reserve_input()
    in_progress = adapter.list_items(state=State.IN_PROGRESS)
    assert len(in_progress) == 1


def test_delete_item(adapter):
    """Test deleting items."""
    item_id = adapter.seed_input(payload={"data": "test"})
    adapter.add_file(item_id, "test.txt", "test.txt", b"content")

    adapter.delete_item(item_id)

    with pytest.raises(ValueError):
        adapter.get_item(item_id)


def test_queue_stats(adapter):
    """Test queue statistics."""
    adapter.seed_input()
    adapter.seed_input()
    item_id = adapter.seed_input()

    adapter.reserve_input()
    adapter.release_input(item_id, State.DONE)

    stats = adapter.get_queue_stats()
    assert stats["pending"] == 2
    assert stats["done"] == 1
    assert stats["total"] == 3
