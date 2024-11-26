import os
import zlib
import shutil
import tempfile
from git_dependency_visualizer import (
    read_git_object,
    parse_commit_data,
    read_tree,
    find_file_in_tree,
    list_git_objects,
    find_commits,
    build_dependency_graph,
    generate_graphviz,
    verify_repo_path,
)

def setup_temporary_repo():
    """Создаёт временную директорию с тестовым Git-репозиторием."""
    repo_path = tempfile.mkdtemp()
    git_objects_path = os.path.join(repo_path, ".git", "objects")
    os.makedirs(git_objects_path)
    return repo_path

def cleanup_temporary_repo(repo_path):
    """Удаляет временную директорию."""
    shutil.rmtree(repo_path)

def test_read_git_object():
    print("Тест: read_git_object")
    repo_path = setup_temporary_repo()
    try:
        object_hash = "abcdef1234567890abcdef1234567890abcdef12"
        object_path = os.path.join(repo_path, ".git", "objects", object_hash[:2])
        os.makedirs(object_path, exist_ok=True)

        # Создаем правильное сжатое содержимое объекта
        raw_data = (
            b"commit 173\0"
            b"tree abcdef1234567890abcdef1234567890abcdef12\n"
            b"parent 1234567890abcdef1234567890abcdef123456\n"
            b"author John Doe <johndoe@example.com> 1638299773 +0000\n"
            b"committer John Doe <johndoe@example.com> 1638299773 +0000\n\n"
            b"Initial commit\n"
        )
        compressed_data = zlib.compress(raw_data)

        # Сохраняем объект в нужное место
        with open(os.path.join(object_path, object_hash[2:]), "wb") as f:
            f.write(compressed_data)

        # Проверяем функцию read_git_object
        header, data = read_git_object(repo_path, object_hash)
        assert header == "commit", f"Expected 'commit', got {header}"
        assert b"tree abcdef1234567890abcdef1234567890abcdef12" in data
        print("✓ Успех")
    finally:
        cleanup_temporary_repo(repo_path)

if __name__ == "__main__":
    test_read_git_object()
    print("Все тесты успешно выполнены!")
