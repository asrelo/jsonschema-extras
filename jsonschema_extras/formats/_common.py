from collections.abc import Callable, Iterable, Sequence
from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:
    from jsonschema import FormatChecker


#: Format checking function.
#:
#: Note:
#:     Any exceptions the function raises on an invalid data value are part
#:     of the function's contract for :class:`~jsonschema.FormatChecker`.
#:
#: Args:
#:     object: a data value to validate
#:
#: Returns:
#:     bool: whether the object is valid for the format
type FormatCheckFn = Callable[[object], bool]


class FormatCheckingFuncInfo(NamedTuple):
    """Data needed to register a format checking function
    in a :class:`~jsonschema.FormatChecker`.

    Attributes:
        format: Exact name of the format for JSON Schema.
        func:
            Function that checks if a JSON data value satisfies a format.
        raises:
            Type(s) of exceptions raised by `func` on an invalid value.
            Exceptions of other types are immediately propagated.
            See :meth:`~jsonschema.FormatChecker.checks` for details.
    """
    format: str
    func: FormatCheckFn
    raises: type[Exception] | tuple[type[Exception], ...] = ()


def register_func_in_checker(
    checker: 'FormatChecker', func_info: FormatCheckingFuncInfo,
) -> FormatCheckFn:
    """Register a format checking function
    in a :class:`~jsonschema.FormatChecker`.

    Utility function working with :class:`FormatCheckingFuncInfo`.

    Args:
        checker (jsonschema.FormatChecker): A `format` property checker.
        func_info (FormatCheckingFuncInfo):
            Data needed to register a format checking function.

    Returns:
        `func_info.func`
    """
    return checker.checks(func_info.format, func_info.raises)(func_info.func)


def register_funcs_in_checker(
    checker: 'FormatChecker', funcs_info: Iterable[FormatCheckingFuncInfo],
) -> Sequence[FormatCheckFn]:
    """Register multiple format checking functions
    in a :class:`~jsonschema.FormatChecker`.

    Args:
        checker (jsonschema.FormatChecker): A `format` property checker.
        funcs_info (Iterable[FormatCheckingFuncInfo]):
            Instances of data needed to register formatt checking functions.

    Returns:
        sequence of `func_info.func` objects
    """
    return [register_func_in_checker(checker, func_info) for func_info in funcs_info]
