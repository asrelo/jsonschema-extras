from collections.abc import Callable, Collection, Iterable
from typing import Generic
from urllib.parse import urlunsplit

from referencing import Resource
from referencing.exceptions import NoSuchResource
from referencing.typing import Retrieve

from jsonschema_extras._util.uri import (
    RPURIBNotRelativeValueError,
    rpurib_split_and_validate_uri,
    rpurib_split_and_validate_uri_base,
    translate_uri_base_splits_validated,
)
from jsonschema_extras.typing import D


# NOTE: satisfies Retrieve[D]
class RetrieversChain(list[Retrieve[D]], Generic[D]):
    """Chain of :class:`~referencing.typing.Retrieve` callables that attempts
    each retriever in order until one succeeds.

    Warning:
        The chain is based on :class:`list`, so it is mutable
        (and has all methods of :class:`list`). If you mutate it
        *after* passing to a :class:`~referencing.Registry`, make sure you know
        what you are doing.

    Allows a user to customize which exceptions are postponed vs raised
    immediately.

    On retrieval failure, provides detailed cause info.

    Parameters:
        retrievers (Iterable[Retrieve[D]]):
            Retriever objects that implement
            :class:`referencing.typing.Retrieve`.
        postpone_excs (Collection[type[BaseException]], optional):
            Exceptions that should trigger a retry with the next retriever.
            :exc:`~referencing.exceptions.NoSuchResource` **is always added
            implicitly** to the collection. Default: ``()``.
        pass_excs (Collection[type[BaseException]], optional):
            Exceptions that should be re‑raised immediately,
            bypassing postponement logic. Default: ``()``.
        should_postpone_exc_fn (Callable[[BaseException], bool], optional):
            Predicate to dynamically decide whether to postpone
            a caught exception (default: ``lambda e: False``).
            (Technically can be used to immediately raise
            :exc:`~referencing.exceptions.NoSuchResource`, whatever you might
            want it for.)
    """

    def __init__(
        self,
        retrievers: Iterable[Retrieve[D]] = (),
        postpone_excs: Collection[type[Exception]] = (),
        pass_excs: Collection[type[Exception]] = (),
        should_postpone_exc_fn: Callable[[Exception], bool] = lambda e: False,
    ):
        super().__init__(retrievers)
        self._postpone_excs = postpone_excs
        self._pass_excs = pass_excs
        self._should_postpone_exc_fn = should_postpone_exc_fn

    @property
    def postpone_excs(self) -> Collection[type[Exception]]:
        """Exposed read‑only view of postpone_excs passed into the constructor."""
        return self._postpone_excs

    @property
    def pass_excs(self) -> Collection[type[Exception]]:
        """Exposed read‑only view of pass_excs passed into the constructor."""
        return self._pass_excs

    @property
    def should_postpone_exc_fn(self) -> Callable[[Exception], bool]:
        """Exposed read‑only view of should_postpone_exc_fn passed
        into the constructor.
        """
        return self._should_postpone_exc_fn

    def __call__(self, uri: str) -> Resource[D]:
        """Retrieve the resource identified by URI using the chained
        retrievers.

        The method iterates over the stored retrievers:
        1. Calls the retriever with `uri`.
        2. If it returns a :class:`~referencing.Resource`,
           the result is returned immediately.
        3. If it raises :exc:~referencing.exceptions.NoSuchResource`
           or any exception listed in :meth:`.postpone_excs`,
           the exception is collected and the loop continues **unless**:
           - the exception type is in :meth:`.pass_excs`, **or**
           - :meth:`.should_postpone_exc_fn` returns ``False``
             for the exception.
           In those cases the exception is re‑raised.
        4. After all retrievers have been tried, an :exc:`ExceptionGroup`
           containing all collected exceptions is raised as the cause
           of a final :exc:`~referencing.exceptions.NoSuchResource`.

        Raises:
            referencing.exceptions.NoSuchResource:
                If the chain is empty (has a :exc:`RuntimeError` as cause)
                or if all retrievers fail (has an :exc:`ExceptionGroup` listing
                all exceptions from retrievers).
        """
        if len(self) == 0:
            cause = RuntimeError('The chain of retrievers is empty')
            raise NoSuchResource(uri) from cause
        exc_types_to_postpone: tuple[type[Exception], ...] = (
            NoSuchResource, *self._postpone_excs,
        )
        excs: list[Exception] = []
        for retrieve in self:
            try:
                return retrieve(uri)
            except exc_types_to_postpone as err:
                if (
                    (
                        (len(self._pass_excs) > 0)
                        and isinstance(err, tuple(self._pass_excs))
                    )
                    or (not self._should_postpone_exc_fn(err))
                ):
                    raise
                excs.append(err)
        exc_group = ExceptionGroup(
            (
                f'All {len(self)!r} retrievers in the chain'
                f' failed to retrieve the resource'
            ),
            excs,
        )
        raise NoSuchResource(uri) from exc_group


class _RetrievalURITranslatorImpl(Generic[D]):

    def __init__(self, retrieve: Retrieve[D], uri_base_old: str, uri_base_new: str):
        self._retrieve = retrieve
        self._uri_base_old_split = rpurib_split_and_validate_uri_base(uri_base_old)
        self._uri_base_new_split = rpurib_split_and_validate_uri_base(uri_base_new)

    @property
    def retrieve_orig(self) -> Retrieve[D]:
        return self._retrieve

    def __call__(self, uri: str) -> Resource[D]:
        uri_split = rpurib_split_and_validate_uri(uri)
        try:
            uri_new_split = translate_uri_base_splits_validated(
                uri_split, self._uri_base_old_split, self._uri_base_new_split,
            )
        except RPURIBNotRelativeValueError:
            uri_new = uri
        else:
            uri_new = urlunsplit(uri_new_split)
        return self._retrieve(uri_new)


class RetrievalURITranslator(Generic[D]):
    """Decorator for a :class:`~referencing.typing.Retrieve` callable
    translating URIs that match with a given old base URI to a new base URI.

    When retrieving a resource, this decorator attempts to resolve the portion
    of the URI relative to the old base URI. If successful, it rewrites and
    appends this portion to the new base URI. If translation fails, it either
    falls back to the original URI (if `allow_old` is True) or immediately
    raises :exc:`~referencing.exceptions.NoSuchResource`.

    Both base URIs and specific schema URIs are **restricted**:
    each must have a scheme and a path, and **no** other components
    are allowed (i.e. **no** credentials, netloc, query, fragment).
    "Parent" segments ``..`` in the path of a schema URI are prohibited.
    All of the above properties are validated.

    Parameters:
        retrieve (Retrieve[D]):
            Retriever object that implements
            :class:`referencing.typing.Retrieve`.
        uri_base_old (str): "Old" base URI.
        uri_base_new (str): "New" base URI.
        allow_old (bool, optional):
            If ``True`` and retrieval by a translated URI fails,
            also tries the original URI. Default: ``False``.
    """

    @classmethod
    def _build_retrievers_chain(
        cls, retrieve: Retrieve[D], uri_base_old: str, uri_base_new: str,
        *, allow_old: bool = False,
    ) -> RetrieversChain[D]:
        retrievers: list[Retrieve[D]] = [
            _RetrievalURITranslatorImpl(retrieve, uri_base_old, uri_base_new),
        ]
        if allow_old:
            retrievers.append(retrieve)
        return RetrieversChain(retrievers)

    def __init__(
        self, retrieve: Retrieve[D], uri_base_old: str, uri_base_new: str,
        *, allow_old: bool = False,
    ):
        self._retrieve = self._build_retrievers_chain(
            retrieve, uri_base_old, uri_base_new, allow_old=allow_old,
        )

    def __call__(self, uri: str) -> Resource[D]:
        return self._retrieve(uri)
