from pathlib import Path

from storage.local import LocalStorage


def test_local_storage_can_save_read_list_and_delete(tmp_path: Path):
    storage = LocalStorage(tmp_path)

    saved_path = storage.save_file("documents/example.txt", b"hello")

    assert saved_path == "documents/example.txt"
    assert storage.get_file("documents/example.txt") == b"hello"
    assert storage.list_files("documents") == ["documents/example.txt"]

    storage.delete_file("documents/example.txt")

    assert storage.list_files("documents") == []
