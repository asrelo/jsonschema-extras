from pathlib import Path
from shutil import rmtree


def purge_directory(path):
    for item in Path(path).glob('*'):
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            rmtree(item)
