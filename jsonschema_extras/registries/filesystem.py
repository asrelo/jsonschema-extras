"""Utilities for accessing schemas on a local filesystem.

Functions in this module match up a path to a directory on a filesystem
(root of local schemas hierarchy) with a base URI for schemas. When retrieving
a schema by its URI, they compute the portion relative to the specified
base URI and use it as a path relative to the specified filesystem root path
to locate the schema file.

Both the base URI and specific schema URIs are **restricted**:
each must have the scheme ``file:`` and a path, **no** other components
are allowed (i.e. **no** credentials, netloc, query, fragment).
"Parent" segments ``..`` in the path of a schema URI are prohibited.
All of the above properties are validated by this module's functions.
"""

from functools import partial
from os import PathLike
from pathlib import PurePosixPath, PurePath, Path
from typing import Any, cast
from urllib.parse import SplitResult, unquote, urlsplit

from referencing.exceptions import NoSuchResource
from referencing.typing import Retrieve

from jsonschema_extras._common import Kwargs, validate_kwargs
from jsonschema_extras._util import coerce_to_dict
from jsonschema_extras.typing import D
from .retrieval import (
    ResourceFromContentsFn,
    RESOURCE_FROM_CONTENTS_FN_DEFAULT,
    CacheFn,
    CacheSpecDefault,
    to_maybe_cached_resource,
)
from .retrieval._common import LoadTextFn
from .retrieval.json import LOADS_FN_JSON_DEFAULT


__all__ = (
    'RESOURCE_FROM_CONTENTS_FN_DEFAULT',
    'LOADS_FN_JSON_DEFAULT',
    'NoSuchResourceFromValueError',
    'file_path_from_uri_by_base',
    'retrieve_text_from_filesystem',
    'build_schemas_from_filesystem_retriever',
)


def split_and_validate_uri_base(uri_base: str) -> SplitResult:
    # here scheme is a default value:
    uri_base_split = urlsplit(uri_base, scheme='')
    if uri_base_split.scheme != 'file':
        raise ValueError(
            f'base URI should have scheme \'file:\', got: {uri_base_split.scheme!r}'
        )
    if uri_base_split.netloc:
        raise ValueError('base URI should not have a netloc')
    if (uri_base_split.username is not None) or (uri_base_split.password is not None):
        raise ValueError('base URI should not have credentials')
    if unquote(uri_base_split.query):
        raise ValueError('base URI should not have a query')
    if uri_base_split.fragment:
        raise ValueError('base URI should not have a fragment')
    return uri_base_split


# XXX: !?
class NoSuchResourceFromValueError(ValueError):
    """:exc:`ValueError` in a schema's URI that should be interpreted
    as absence of the resource.
    """


def split_and_validate_uri(uri: str) -> SplitResult:
    uri_split = urlsplit(uri, scheme='')
    if uri_split.scheme != 'file':
        raise ValueError(f'URI should have \'file:\' scheme, got: {uri_split.scheme!r}')
    if uri_split.netloc:
        raise ValueError('URI should not have a netloc')
    if (uri_split.username is not None) or (uri_split.password is not None):
        raise ValueError('URI should not have credentials')
    if uri_split.fragment:
        raise ValueError('URI should not have a fragment')
    if unquote(uri_split.query):
        raise NoSuchResourceFromValueError('URI should not have a query')
    return uri_split


def _relative_path_from_uri_by_base(
    uri: str, uri_base: str | SplitResult,
) -> PurePosixPath:
    if not isinstance(uri_base, SplitResult):
        # XXX: ValueError s are propagated
        uri_base_split = split_and_validate_uri_base(uri_base)
    else:
        uri_base_split = uri_base
    uri_split = split_and_validate_uri(uri)  # XXX: ValueError s are propagated
    uri_path = PurePosixPath(unquote(uri_split.path))
    uri_base_path = PurePosixPath(unquote(uri_base_split.path))
    try:
        return uri_path.relative_to(uri_base_path, walk_up=False)
    except ValueError as err:
        raise NoSuchResourceFromValueError(str(err)) from err


def _file_path_from_uri_by_base_internal(
    uri: str, uri_base: str | SplitResult, path: str | PathLike[str],
) -> PurePath:
    return (PurePath(path) / _relative_path_from_uri_by_base(uri, uri_base))


def file_path_from_uri_by_base(
    uri: str, uri_base: str, path: str | PathLike[str],
) -> PurePath:
    """Computes the file path of a locally stored schema based on its URI.

    Maps a URI under `uri_base` to a file under `path`. See the rules
    of this mapping and **restrictions on URIs** in description
    of :mod:`jsonschema_extras.registries.filesystem`.

    Args:
        uri (str):  URI of the schema to retrieve.
            Should be relative to `uri_base`,
            otherwise :exc:`~referencing.exceptions.NoSuchResource` is raised.
            Must have the scheme ``file:`` and a path
            (with no "parent" segments ``..``), **no** other components
            are allowed (i.e. **no** credentials, netloc, query, fragment).
        uri_base (str):
            Base URI corresponding to the filesystem root.
            Must have the scheme ``file:`` and a path, **no** other components
            are allowed (i.e. **no** credentials, netloc, query, fragment).
        path (str | PathLike[str]):
            Root filesystem path containing the schemas.

    Returns:
        Path under `path` to the schema on the filesystem.

    Raises:
        NoSuchResourceFromValueError:
            URI resolution relative to the base URI failed.
        ValueError: On invalid `uri` or `uri_base`.

    Examples:
        >>> file_path_from_uri_by_base(
        ...     'file:/schemas/person.json',
        ...     'file:/schemas/',
        ...     '/var/data/schemas',
        ... ).as_posix()
        '/var/data/schemas/person.json'

        >>> file_path_from_uri_by_base(
        ...     'file:/schemas/definitions/address.json',
        ...     'file:/schemas/',
        ...     '/var/data/schemas',
        ... ).as_posix()
        '/var/data/schemas/definitions/address.json'
    """
    return _file_path_from_uri_by_base_internal(uri, uri_base, path)


def _retrieve_text_from_filesystem_internal(
    uri: str, uri_base: str | SplitResult, path: str | PathLike[str],
    *, open_kwargs: Kwargs | None = None,
) -> str:
    if open_kwargs is not None:
        open_kwargs = coerce_to_dict(open_kwargs)
    else:
        open_kwargs = {}
    open_kwargs = cast(
        dict[str, Any],
        validate_kwargs(
            open_kwargs, allowed=('buffering', 'encoding', 'errors', 'newline'),
        ),
    )
    open_kwargs.setdefault('encoding', 'utf-8')
    try:
        with open(
            Path(_file_path_from_uri_by_base_internal(uri, uri_base, path)),
            'rt',
            **open_kwargs,
        ) as file:
            return file.read()  # type: ignore[no-any-return]
    except (NoSuchResourceFromValueError, FileNotFoundError) as err:
        raise NoSuchResource(uri) from err


def retrieve_text_from_filesystem(
    uri: str, uri_base: str, path: str | PathLike[str],
    *, open_kwargs: Kwargs | None = None,
) -> str:
    """Retrieves text of a schema on a filesystem under a specified root.

    Maps URIs under `uri_base` to files under `path`. See the rules
    of this mapping and **restrictions on URIs** in description
    of :mod:`jsonschema_extras.registries.filesystem`.

    Args:
        uri (str):  URI of the schema to retrieve.
            Should be relative to `uri_base`,
            otherwise :exc:`~referencing.exceptions.NoSuchResource` is raised.
            Must have the scheme ``file:`` and a path
            (with no "parent" segments ``..``), **no** other components
            are allowed (i.e. **no** credentials, netloc, query, fragment).
        uri_base (str):
            Base URI corresponding to the filesystem root.
            Must have the scheme ``file:`` and a path, **no** other components
            are allowed (i.e. **no** credentials, netloc, query, fragment).
        path (str | PathLike[str]):
            Root filesystem path containing the schemas.
        open_kwargs (Mapping[str, Any], optional):
            Keyword arguments to pass to Python built-in function :func:`open`.
            Allowed arguments: ``buffering``,
            ``encoding`` (default: ``'utf-8'``), ``errors``, ``newline``.

    Returns:
        Text (serialized representation) of the schema loaded
        from the filesystem.

    Raises:
        referencing.exceptions.NoSuchResource:
            If a schema by the given URI does not exist (URI resolution
            relative to the base URI failed
            (has a :exc:`NoSuchResourceFromValueError` as cause),
            or the file was not found on the filesystem
            (has :exc:`FileNotFoundError` as cause).
        OSError:
            If the file cannot be opened for a reason other
            than it was not found. Passed through from the Python built-in
            function :func:`open`.
        ValueError:
            On invalid `uri` or `uri_base`.
            **OR** If there was an encoding error when reading the file
            (passed through from the Python built-in function :func:`open`).
        TypeError:
            If there are arguments in `open_kwargs` other than allowed
            arguments.
    """
    return _retrieve_text_from_filesystem_internal(
        uri, uri_base, path, open_kwargs=open_kwargs,
    )


def build_schemas_from_filesystem_retriever(
    uri_base: str,
    path: str | PathLike[str],
    *, open_kwargs: Kwargs | None = None,
    cache: CacheFn[D] | CacheSpecDefault | None = None,
    loads: LoadTextFn[D] = LOADS_FN_JSON_DEFAULT,
    from_contents: ResourceFromContentsFn[D] = RESOURCE_FROM_CONTENTS_FN_DEFAULT,
) -> Retrieve[D]:
    """Returns a new retrieval callable for schemas on a filesystem
    under a specified root.

    The returned retriever maps URIs under `uri_base` to files under `path`.
    See the rules of this mapping and **restrictions on URIs** in description
    of :mod:`jsonschema_extras.registries.filesystem`.

    Args:
        uri_base (str):
            Base URI corresponding to the filesystem root.
            Must have the scheme ``file:`` and a path, **no** other components
            are allowed (i.e. **no** credentials, netloc, query, fragment).
        path (str | PathLike[str]):
            Root filesystem path containing the schemas.
        open_kwargs (Mapping[str, Any], optional):
            Keyword arguments to pass to Python built-in function :func:`open`.
            Allowed arguments: ``buffering``,
            ``encoding`` (default: ``'utf-8'``), ``errors``, ``newline``.
        cache (CacheFn | CacheSpecDefault, optional):
            Caching decorator for :class:`~referencing.typing.Retrieve`,
            or ``'default'`` to use the default caching implementation
            (see description of :mod:`jsonschema_extras.registries.retrieval`
            for details). Defaults to ``None``, meaning no caching.
        loads (LoadTextFn, optional):
            Function to deserialize resource contents (for example,
            JSON data structure from JSON string).
            Default: :obj:`~.retrieval.json.LOADS_FN_JSON_DEFAULT` (for JSON).
        from_contents (ResourceFromContentsFn, optional):
            Function to produce a :class:`~referencing.Resource`
            from deserialized resource contents.
            Default: :meth:`~referencing.Resource.from_contents`.

    Returns:
        A :class:`~referencing.typing.Retrieve` callable that resolves
        schema URIs under `uri_base` from files under `path`
        (with caching, if instructed so).

    Raises:
        ValueError: On invalid `uri_base`.
        TypeError:
            If there are arguments in `open_kwargs` other than allowed
            arguments.
    """
    uri_base_split = split_and_validate_uri_base(uri_base)
    retrieve_text_from_filesystem_fn = partial(
        _retrieve_text_from_filesystem_internal,
        uri_base=uri_base_split, path=path, open_kwargs=open_kwargs,
    )
    return to_maybe_cached_resource(
        cache, loads=loads, from_contents=from_contents,
    )(retrieve_text_from_filesystem_fn)
