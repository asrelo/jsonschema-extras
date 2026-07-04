"""Utilities for working with the JSON Schema Python library
`jsonschema <https://pypi.org/project/jsonschema/>`__.

Features:

- :doc:`Schemas bundled with the library </schemas>`

- :doc:`Formats bundled with the library </formats>`

- :doc:`Utilities for accessing schemas on a filesystem </filesystem>`

- :class:`~jsonschema_extras.registries.RetrieveFunctionsChain` -
  chain of responsibility composed of retriever functions
  (used to initialize :class:`referencing.Registry`).
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
    'BUNDLED_SCHEMAS_URI_BASE_DEFAULT',
    'bundled_schemas_retriever',
)


def bundled_schemas_files() -> Traversable:
    """Returns a :class:`~importlib.resources.abc.Traversable` object
    containing resources for bundled schemas.

    Built upon :func:`importlib.resources.files`.
    """
    return (importlib.resources.files('jsonschema_extras') / 'schemas')


#: Default base URI for schemas bundled with this library.
BUNDLED_SCHEMAS_URI_BASE_DEFAULT: Final[str] = 'file:/jsonschema_extras/schemas'

_BUNDLED_SCHEMAS_ENCODING: Final = 'utf-8'


@contextmanager
def bundled_schemas_retriever(
    *, uri_base: str = BUNDLED_SCHEMAS_URI_BASE_DEFAULT,
    open_buffering: int = -1,
    cache: CacheFn[Any] | CacheSpecDefault | None = None,
) -> Iterator[Retrieve]:
    """**Context manager** producing a retrieval callable for this library's
    bundled schemas.

    Warning:
        The produced retriever is only valid within duration of an explicit
        lifecycle, hence the context manager.

    Args:
        uri_base (str):
            Base URI for bundled schemas. Must have the scheme ``file:``
            and a path, **no** other components are allowed
            (i.e. **no** credentials, netloc, query, fragment).
            Default: :data:`BUNDLED_SCHEMAS_URI_BASE_DEFAULT`.
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
            uri_base,
            bundled_schemas_path,
            open_kwargs=dict(
                buffering=open_buffering, encoding=_BUNDLED_SCHEMAS_ENCODING,
            ),
            cache=cache,
            loads=LOADS_FN_JSON_DEFAULT,
        )
