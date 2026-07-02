from collections.abc import Callable, Collection
from typing import Generic, TypeVar

from referencing import Resource
from referencing.exceptions import NoSuchResource
from referencing.typing import Retrieve


__all__ = (
    'RetrieveFunctionsChain',
)


D = TypeVar('D')


# NOTE: satisfies Retrieve[D]
class RetrieveFunctionsChain(list[Retrieve[D]], Generic[D]):
    '''Chain of :class:`~referencing.typing.Retrieve` callables that attempts
    each retriever in order until one succeeds.

    Warning:
        The chain is based on `list`, so it is mutable (and has all methods
        of `list`). If you mutate it *after* passing
        to a :class:`~referencing.Registry`, make sure you know
        what you are doing.

    Allows a user to customize which exceptions are postponed vs raised
    immediately.

    On retrieval failure, provides detailed cause info.

    Parameters:
        *retrievers (Retrieve[D]):
            Retriever objects that implement
            :class:`referencing.typing.Retrieve`.
        postpone_excs (Collection[type[BaseException]], optional):
            Exceptions that should trigger a retry with the next retriever.
            :exc:`~referencing.exceptions.NoSuchResource` **is always added
            implicitly** to the collection. Default: `()`.
        pass_excs (Collection[type[BaseException]], optional):
            Exceptions that should be re‑raised immediately,
            bypassing postponement logic. Default: `()`.
        should_postpone_exc_fn (Callable[[BaseException], bool], optional):
            Predicate to dynamically decide whether to postpone
            a caught exception (default: `lambda e: False`).
            (Technically can be used to immediately raise
            :exc:`~referencing.exceptions.NoSuchResource`, whatever you might
            want it for.)
    '''

    def __init__(
        self,
        *retrievers: Retrieve[D],
        postpone_excs: Collection[type[BaseException]] = (),
        pass_excs: Collection[type[BaseException]] = (),
        should_postpone_exc_fn: Callable[[BaseException], bool] = lambda e: False,
    ):
        super().__init__(retrievers)
        self._postpone_excs = postpone_excs
        self._pass_excs = pass_excs
        self._should_postpone_exc_fn = should_postpone_exc_fn

    @property
    def postpone_excs(self) -> Collection[type[BaseException]]:
        '''Exposed read‑only view of postpone_excs passed
        into :meth:`__init__`.'''
        return self._postpone_excs

    @property
    def pass_excs(self) -> Collection[type[BaseException]]:
        '''Exposed read‑only view of pass_excs passed into :meth:`__init__`.'''
        return self._pass_excs

    @property
    def should_postpone_exc_fn(self) -> Callable[[BaseException], bool]:
        '''Exposed read‑only view of should_postpone_exc_fn passed
        into :meth:`__init__`.'''
        return self._should_postpone_exc_fn

    def __call__(self, uri: str) -> Resource[D]:
        '''Retrieve the resource identified by `uri` using the chained
        retrievers.

        The method iterates over the stored retrievers:
        1. Calls the retriever with `uri`.
        2. If it returns a :class:`~referencing.Resource`,
           the result is returned immediately.
        3. If it raises :exc:~referencing.exceptions.NoSuchResource`
           or any exception listed in :meth:`.postpone_excs`,
           the exception is collected and the loop continues **unless**:
           - the exception type is in :meth:`.pass_excs`, **or**
           - :meth:`.should_postpone_exc_fn` returns `False` for the exception.
           In those cases the exception is re‑raised.
        4. After all retrievers have been tried, an `ExceptionGroup`
           containing all collected exceptions is raised as the cause
           of a final :exc:`~referencing.exceptions.NoSuchResource`.

        Raises:
            referencing.exceptions.NoSuchResource:
                If the chain is empty (has a `RuntimeError` as cause)
                or if all retrievers fail (has an `ExceptionGroup` listing
                all exceptions from retrievers).
        '''
        if len(self) == 0:
            cause = RuntimeError('The chain of retrievers is empty')
            raise NoSuchResource(uri) from cause
        excs = []
        for retrieve in self:
            try:
                return retrieve(uri)
            except (NoSuchResource, *self._postpone_excs) as err:
                if (
                    ((len(self._pass_excs) > 0) and isinstance(err, tuple(self._pass_excs)))
                    or (not self._should_postpone_exc_fn(err))
                ):
                    raise
                excs.append(err)
        exc_group = ExceptionGroup(
            f'All {len(self)!r} retrievers in the chain failed to retrieve the resource', excs
        )
        raise NoSuchResource(uri) from exc_group
