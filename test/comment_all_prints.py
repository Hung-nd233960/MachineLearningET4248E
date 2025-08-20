import sys
from pathlib import Path


def comment_prints_in_file(file_path: Path, backup_root: Path):
    rel_path = file_path.relative_to(backup_root.parent)
    backup_file = backup_root / rel_path
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    # Move original to backup
    file_path.rename(backup_file)
    # print(f"Backed up: {backup_file}")

    with (
        open(backup_file, "r", encoding="utf-8") as fin,
        open(file_path, "w", encoding="utf-8") as fout,
    ):
        for line in fin:
            stripped = line.lstrip()
            if stripped.startswith("print(") or stripped.startswith("print "):
                indent = len(line) - len(stripped)
                fout.write(" " * indent + "#" + stripped)
            else:
                fout.write(line)


def recursive_process(root: Path):
    backup_root = root / ".backup"
    backup_root.mkdir(exist_ok=True)
    for py_file in root.rglob("*.py"):
        # Skip files inside .backup folder to avoid infinite loop
        if ".backup" in py_file.parts:
            continue
        comment_prints_in_file(py_file, backup_root)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # print("Usage: python comment_prints.py <folder>")
        sys.exit(1)
    root_dir = Path(sys.argv[1])
    if not root_dir.is_dir():
        # print(f"Not a directory: {root_dir}")
        sys.exit(1)

    recursive_process(root_dir)
    # print("Done processing all .py files recursively.")
