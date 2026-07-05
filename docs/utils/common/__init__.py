from collections.abc import Iterable
from itertools import repeat
from pathlib import Path
from shutil import rmtree


class _ZipSentinel:
    pass


_ZIP_SENTINEL = _ZipSentinel()


# This is a replacement for the following idiom:
#     a, b = zip(*iterables, strict=True)
# This idiom is problematic because when `iterables` turns out to have length 0,
# zip has no idea how many items to yield and yields 0,
# which is not unpackable into `a, b`.
# The alternative code with this function:
#     a, b = zip_n(*iterables, n=2)
# Keep in mind that it does check the number of items in each iterable.
def zip_n(*iterables, n) -> Iterable[tuple]:
    n = max(n, 0)
    if len(iterables) == 0:
        yield from repeat((), n)
        return
    iterators = list(map(iter, iterables))
    for i in range(n):
        tup = tuple(next(it, _ZIP_SENTINEL) for it in iterators)
        if any(isinstance(v, _ZipSentinel) for v in tup):
            raise ValueError(
                f'at least one of iterables was exhausted in {i + 1} < {n} iterations'
            )
        yield tup


def purge_directory(path):
    for item in Path(path).glob('*'):
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            rmtree(item)
