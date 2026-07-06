'''Helpers related to resource retrieval.

For the default implementation of resource caching,
see :func:`referencing.retrieval.to_cached_resource`.
It uses `lru_cache(maxsize=None)` as of version 0.37 .
'''

from collections.abc import Callable
from typing import Literal, TypeVar

from referencing import Resource
from referencing.retrieval import to_cached_resource as original_to_cached_resource
from referencing.typing import Retrieve

from ._common import *
from .json import * # XXX: ?


__all__ = (
    'LoadTextFn',
    'RetrieveTextFn',
    'ResourceFromContentsFn',
    'RESOURCE_FROM_CONTENTS_FN_DEFAULT',
    'CacheFn',
    'CacheSpecDefault',
    'to_resource',
    'to_cached_resource',
    'to_maybe_cached_resource',
)


D = TypeVar('D')


#: Function to retrieve serialized resource data by URI
#:
#: Args:
#:     str: Resource URI.
#:
#: Returns:
#:     str: Retrieved serialized resource representation.
type RetrieveTextFn = Callable[[str], str]


#: Function to make a :class:`~referencing.Resource` from resource contents.
#:
#: Note:
#:     The function is intended to take a deserialized data structure.
#:
#: Args:
#:     D: Resource contents.
#:
#: Returns:
#:     Resource[D]: Produced :class:`~referencing.Resource` instance.
type ResourceFromContentsFn[D] = Callable[[D], Resource[D]]

#: Default implementation of :data:`ResourceFromContentsFn`
#:
#: Uses the default :meth:`~referencing.Resource.from_contents` strategy.
RESOURCE_FROM_CONTENTS_FN_DEFAULT: Final[ResourceFromContentsFn] = Resource.from_contents


#: Function decorator for :class:`~reference.typing.Retrieve`
#: to cache retrieved resources by their URIs.
type CacheFn[D] = Callable[[Retrieve[D]], Retrieve[D]]

#: Specification for default implementation of caching for retrieved resources.
type CacheSpecDefault = Literal['default']


def to_resource(
    loads: LoadTextFn[D] = LOADS_FN_JSON_DEFAULT,
    from_contents: ResourceFromContentsFn[D] = RESOURCE_FROM_CONTENTS_FN_DEFAULT,
) -> Callable[[RetrieveTextFn], Retrieve[D]]:
    '''Build a decorator to make a resource retrieval callable
    out of a :data:`RetrieveTextFn`.

    :data:`RetrieveTextFn` retrieves serialized representation by URI.
    A decorator produced by this function adds deserialization (`loads`),
    creating a :class:`~referencing.Resource` (with no caching).

    Args:
        loads (LoadTextFn, optional):
            Function to deserialize resource contents (for example,
            JSON data structure from JSON string).
            Default: :data:`~.retrieval.json.LOADS_FN_JSON_DEFAULT` (for JSON).
        from_contents (ResourceFromContentsFn, optional):
            Function to produce a :class:`~referencing.Resource`
            from deserialized resource contents.
            Default: :meth:`~referencing.Resource.from_contents`.

    Returns:
        Decorator taking a text retriever :data:`RetrieveTextFn`
        and returning a caching resource retriever.
    '''
    if from_contents is None:
        from_contents = Resource.from_contents
    def decorator(retrieve: RetrieveTextFn) -> Retrieve[D]:
        def wrapped_retrieve(uri: str) -> Resource[D]:
            response = retrieve(uri)
            contents = loads(response)
            return from_contents(contents)
        return wrapped_retrieve
    return decorator


def to_cached_resource(
    cache: CacheFn[D] | None = None,
    loads: LoadTextFn[D] = LOADS_FN_JSON_DEFAULT,
    from_contents: ResourceFromContentsFn[D] = RESOURCE_FROM_CONTENTS_FN_DEFAULT,
) -> Callable[[RetrieveTextFn], Retrieve[D]]:
    '''Build a decorator to make a resource retrieval callable
    out of a :data:`RetrieveTextFn` with caching.

    :data:`RetrieveTextFn` retrieves serialized representation by URI.
    A decorator produced by this function adds deserialization (`loads`),
    creating a :class:`~referencing.Resource` and caching.

    Args:
        cache (CacheFn[D], optional):
            Caching decorator for :class:`~referencing.typing.Retrieve`,
            or `None` to use the default caching implementation
            (see :func:`referencing.retrieval.to_cached_resource`).
            Defaults to `None`.
        loads (LoadTextFn, optional):
            Function to deserialize resource contents (for example,
            JSON data structure from JSON string).
            Default: :data:`~.retrieval.json.LOADS_FN_JSON_DEFAULT` (for JSON).
        from_contents (ResourceFromContentsFn, optional):
            Function to produce a :class:`~referencing.Resource`
            from deserialized resource contents.
            Default: :meth:`~referencing.Resource.from_contents`.

    Returns:
        Decorator taking a text retriever :data:`RetrieveTextFn`
        and returning a caching resource retriever.
    '''
    kwargs_extra = {}
    if from_contents is not None:
        kwargs_extra['from_contents'] = from_contents
    return original_to_cached_resource(cache=cache, loads=loads, **kwargs_extra)


def to_maybe_cached_resource(
    cache: CacheFn[D] | CacheSpecDefault | None = None,
    loads: LoadTextFn[D] = LOADS_FN_JSON_DEFAULT,
    from_contents: ResourceFromContentsFn[D] = RESOURCE_FROM_CONTENTS_FN_DEFAULT,
) -> Callable[[RetrieveTextFn], Retrieve[D]]:
    '''Build a decorator to make a resource retrieval callable
    out of a :data:`RetrieveTextFn` with optional caching.

    :data:`RetrieveTextFn` retrieves serialized representation by URI.
    A decorator produced by this function adds deserialization (`loads`),
    creating a :class:`~referencing.Resource` and optional caching.

    Args:
        cache (CacheFn[D] | CacheSpecDefault, optional):
            Caching decorator for :class:`~referencing.typing.Retrieve`,
            or `'default'` to use the default caching implementation
            (see :func:`referencing.retrieval.to_cached_resource`).
            Defaults to `None`, meaning no caching.
        loads (LoadTextFn, optional):
            Function to deserialize resource contents (for example,
            JSON data structure from JSON string).
            Default: :data:`~.retrieval.json.LOADS_FN_JSON_DEFAULT` (for JSON).
        from_contents (ResourceFromContentsFn, optional):
            Function to produce a :class:`~referencing.Resource`
            from deserialized resource contents.
            Default: :meth:`~referencing.Resource.from_contents`.

    Returns:
        Decorator taking a text retriever :data:`RetrieveTextFn`
        and returning a resource retriever.
    '''
    if cache is None:
        return to_resource(loads=loads, from_contents=from_contents)
    if callable(cache):
        cache_to_pass = cache
    elif cache != 'default':
        raise ValueError(f'Unknown cache specification: {cache!r}')
    else:
        cache_to_pass = None
    return to_cached_resource(cache=cache_to_pass, loads=loads, from_contents=from_contents)
