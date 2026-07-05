"""Utilities for working with the JSON Schema Python library
`jsonschema <https://pypi.org/project/jsonschema/>`__.

Features:

- :doc:`Schemas bundled with the library </schemas>`

- :doc:`Formats bundled with the library </formats>`

- :doc:`Utilities for accessing schemas on a filesystem </filesystem>`

- :doc:`Other generally useful utilities </misc>`
"""

from collections.abc import Iterator
from contextlib import contextmanager
import importlib.resources
from importlib.resources.abc import Traversable
from typing import Any, Final

from referencing.typing import Retrieve

from .registries import build_schemas_from_filesystem_retriever
from .registries.retrieval import CacheFn, CacheSpecDefault
from .registries.retrieval.json import LOADS_FN_JSON_DEFAULT


__all__ = (
    'bundled_schemas_files',
    'BUNDLED_SCHEMAS_URI_BASE',
    'bundled_schemas_retriever',
)


def bundled_schemas_files() -> Traversable:
    """Returns a :class:`~importlib.resources.abc.Traversable` object
    containing resources for bundled schemas.

    Built upon :func:`importlib.resources.files`.
    """
    return (importlib.resources.files('jsonschema_extras') / 'schemas')


#: Base URI for schemas bundled with this library.
#:
#: See Also:
#:     :func:`bundled_schemas_retriever`
BUNDLED_SCHEMAS_URI_BASE: Final[str] = 'file:/jsonschema_extras/schemas'

_BUNDLED_SCHEMAS_ENCODING: Final = 'utf-8'


@contextmanager
def bundled_schemas_retriever(
    *, open_buffering: int = -1, cache: CacheFn[Any] | CacheSpecDefault | None = None,
) -> Iterator[Retrieve]:
    """**Context manager** producing a retrieval callable for this library's
    bundled schemas.

    Warning:
        The produced retriever is only valid within duration of an explicit
        lifecycle, hence the context manager.

    Args:
        cache (CacheFn | CacheSpecDefault, optional):
            Caching decorator for :class:`~referencing.typing.Retrieve`,
            or ``'default'`` to use the default caching implementation
            (see description of :mod:`jsonschema_extras.registries.retrieval`
            for details). Defaults to ``None``, meaning no caching.
        open_buffering (int, optional):
            Optional integer used to set the buffering policy.
            See the Python built-in function :func:`open`.

    Yields:
        A retrieval callable for this library's bundled schemas.
        The retriever is only valid until the context is exited.

    Raises:
        ValueError: On invalid `uri_base`.

    Note:
        The implementation uses :mod:`importlib.resources` which conceptually
        cannot provide a persistent path to a directory which could be accessed
        by common code at any time. The lifecycle has to be explicit
        due to using package resources.
    """
    with importlib.resources.as_file(bundled_schemas_files()) as bundled_schemas_path:
        yield build_schemas_from_filesystem_retriever(
            BUNDLED_SCHEMAS_URI_BASE,
            bundled_schemas_path,
            open_kwargs=dict(
                buffering=open_buffering, encoding=_BUNDLED_SCHEMAS_ENCODING,
            ),
            cache=cache,
            loads=LOADS_FN_JSON_DEFAULT,
        )
