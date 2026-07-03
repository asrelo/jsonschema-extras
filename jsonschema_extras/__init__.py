"""Utilities for working with the JSON Schema Python library
[`jsonschema`](https://pypi.org/project/jsonschema/).

Some features:

- Specific schemas bundled with the library

  To get access to bundled schemas within your project,
  use :func:`bundled_schemas_retriever` to create a retrieval callable to use
  when instantiating :class:`referencing.Registry`.
  (You can use :class:`~.registries.RetrieveFunctionsChain` to chain
  multiple retrivers.)
  Then all bundled schemas will be available via the registry with the base URI
  you passed to :func:`bundled_schemas_retriever`
  (:data:`~BUNDLED_SCHEMAS_URI_BASE_DEFAULT` by default).

- Specific formats bundled with the library
  (along with convenience utilities for using them)

  See :mod:`jsonschema_extras.formats` for usage instructions.

- Utilities for accessing JSON-encoded schemas on a local filesystem
  (:mod:`jsonschema_extras.filesystem`).

- :class:`~.registries.RetrieveFunctionsChain` - chain of responsibility
  composed of retriever functions, is used to initialize
  :class:`referencing.Registry`.
"""

from collections.abc import Iterator
from contextlib import contextmanager
import importlib.resources
from importlib.resources.abc import Traversable
from typing import Final

from referencing.typing import Retrieve

from ._common import *  # noqa: F401,F403
from .registries import build_schemas_from_filesystem_retriever
from .registries.retrieval import CacheFn, CacheSpecDefault
from .registries.retrieval.json import LOADS_FN_JSON_DEFAULT


__all__ = (
    'bundled_schemas_files',
    'BUNDLED_SCHEMAS_URI_BASE_DEFAULT',
    'bundled_schemas_retriever',
)


def bundled_schemas_files() -> Traversable:
    """Returns a :class:`~importlib.abc.Traversable` object
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
    cache: CacheFn | CacheSpecDefault | None = None,
) -> Iterator[Retrieve]:
    """Context manager producing a retrieval callable for this library's
    bundled schemas.

    Warning:
        The produced retriever is only valid within duration an explicit
        lifecycle, hence the context manager.

    Args:
        uri_base (str):
            Base URI for bundled schemas. Must have the scheme `file:`
            and a path, **no** other components are allowed
            (i.e. **no** credentials, netloc, query, fragment).
            Default: :data:`BUNDLED_SCHEMAS_URI_BASE_DEFAULT`.
        cache (CacheFn | CacheSpecDefault, optional):
            Caching decorator for :class:`~referencing.typing.Retrieve`,
            or `'default'` to use the default caching implementation
            (see description of :mod:`jsonschema_extras.registries.retrieval`
            for details). Defaults to `None`, meaning no caching.
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
