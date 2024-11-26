#!/usr/bin/env python3
import os
import zlib
import argparse

def read_git_object(repo_path, object_hash):
    """Читает Git-объект из папки .git/objects."""
    obj_dir = os.path.join(repo_path, ".git", "objects", object_hash[:2])
    obj_file = os.path.join(obj_dir, object_hash[2:])
    with open(obj_file, "rb") as f:
        compressed_data = f.read()
    decompressed_data = zlib.decompress(compressed_data)
    header, data = decompressed_data.split(b"\x00", 1)
    obj_type, _ = header.decode().split(" ", 1)  # Разделяем тип объекта и размер
    return obj_type, data

def parse_commit_data(commit_data):
    """Парсит содержимое коммита и возвращает словарь с данными."""
    lines = commit_data.splitlines()
    metadata = {}
    for line in lines:
        if line == "":
            break
        key, value = line.split(" ", 1)
        metadata[key] = value
    return metadata

def read_tree(repo_path, tree_hash):
    """Читает содержимое дерева Git и возвращает список файлов и их типов."""
    header, data = read_git_object(repo_path, tree_hash)
    if not header.startswith("tree"):
        return []

    files = []
    i = 0
    while i < len(data):
        mode_end = data.find(b" ", i)
        name_end = data.find(b"\x00", mode_end)
        mode = data[i:mode_end].decode("utf-8")
        name = data[mode_end + 1:name_end].decode("utf-8")
        obj_hash = data[name_end + 1:name_end + 21].hex()
        files.append((mode, name, obj_hash))
        i = name_end + 21
    return files

def find_file_in_tree(repo_path, tree_hash, target_file):
    """Рекурсивно ищет файл в дереве."""
    for mode, name, obj_hash in read_tree(repo_path, tree_hash):
        if name == target_file:
            return True  # Файл найден
        if mode == "40000":  # Это подкаталог
            if find_file_in_tree(repo_path, obj_hash, target_file):
                return True
    return False

def list_git_objects(repo_path):
    """Собирает все объекты в репозитории."""
    objects_dir = os.path.join(repo_path, ".git", "objects")
    object_hashes = []
    for root, _, files in os.walk(objects_dir):
        for file in files:
            if len(file) == 38:  # 2 символа + 38 символов хэша
                object_hashes.append(os.path.basename(root) + file)
    return object_hashes

def find_commits(repo_path, target_file):
    """Находит все коммиты, связанные с целевым файлом."""
    commits = []
    objects = list_git_objects(repo_path)
    for obj_hash in objects:
        header, data = read_git_object(repo_path, obj_hash)
        if header.startswith("commit"):
            commit_data = data.decode("utf-8")
            parsed_data = parse_commit_data(commit_data)
            tree_hash = parsed_data.get("tree")
            if tree_hash and find_file_in_tree(repo_path, tree_hash, target_file):
                commits.append(obj_hash)
    return commits

def build_dependency_graph(repo_path, commits):
    """Строит граф зависимостей для коммитов."""
    graph = {}
    for commit_hash in commits:
        header, data = read_git_object(repo_path, commit_hash)
        metadata = parse_commit_data(data.decode("utf-8"))
        parent_hashes = metadata.get("parent", "").split()
        graph[commit_hash] = parent_hashes
    return graph

def generate_graphviz(graph):
    """Генерирует Graphviz код для графа."""
    dot = ["digraph G {"]
    dot.append("    node [shape=box, fontsize=10];")
    for commit, parents in graph.items():
        dot.append(f'    "{commit}" [label="{commit}"];')
        for parent in parents:
            dot.append(f'    "{commit}" -> "{parent}";')
    dot.append("}")
    return "\n".join(dot)

def verify_repo_path(repo_path):
    """Проверяет, что путь является репозиторием Git."""
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"Ошибка: Путь '{repo_path}' не является Git-репозиторием.")
        exit(1)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей Git-репозитория.")
    parser.add_argument(
        "-r", "--repo-path",
        required=True,
        help="Путь к анализируемому Git-репозиторию."
    )
    parser.add_argument(
        "-f", "--target-file",
        required=True,
        help="Имя файла в репозитории для фильтрации коммитов."
    )
    parser.add_argument(
        "-o", "--output-file",
        required=True,
        help="Путь к файлу-результату в виде кода Graphviz."
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Проверка репозитория
    verify_repo_path(args.repo_path)

    # Получение коммитов
    commits = find_commits(args.repo_path, args.target_file)
    if not commits:
        print(f"Коммиты с файлом '{args.target_file}' не найдены.")
        exit(0)

    # Построение графа зависимостей
    graph = build_dependency_graph(args.repo_path, commits)

    # Генерация Graphviz кода
    graphviz_code = generate_graphviz(graph)

    # Запись в файл
    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(graphviz_code)
        print(f"Graphviz код успешно записан в файл '{args.output_file}'.")
    except IOError as e:
        print(f"Ошибка при записи в файл '{args.output_file}': {e}")
        exit(1)

    # Вывод Graphviz кода на экран
    print("\nСгенерированный Graphviz код:\n")
    print(graphviz_code)

if __name__ == "__main__":
    main()
