from collections.abc import Sequence

from jsonschema_extras._util import SEQUENCE_PRIMITIVE_TYPES_DEFAULT
from ._common import FormatCheckingFuncInfo


def is_numbers_range(instance: object) -> bool:
    """Tests if an object is a numbers range (a sequence of 2 numbers
    in non-descending order).

    A numbers range is defined as a sequence containing exactly 2 comparable
    numeric elements where the first element is less than or equal
    to the second element, forming a valid range [min, max].

    Returns:
        bool: Whether `instance` is a numbers range: ascending sequence
        of 2 numbers.

    Examples:

        Valid ranges::

            >>> is_numbers_range([1, 5])
            True
            >>> is_numbers_range([3.14, 3.14])
            True
            >>> is_numbers_range((0, 10))
            True

        Invalid ranges::

            >>> is_numbers_range([5, 1])
            False
            >>> is_numbers_range([1, 2, 3])
            False
            >>> is_numbers_range([1])
            False
            >>> is_numbers_range(5)
            False
    """
    if not (
        isinstance(instance, Sequence)
        and (not isinstance(instance, tuple(SEQUENCE_PRIMITIVE_TYPES_DEFAULT)))
        and (len(instance) == 2)
    ):
        return False
    try:
        return (instance[0] <= instance[1])
    except TypeError:
        return False


#: Format ``numbers-range`` checked by :func:`is_numbers_range`
is_numbers_range_info = FormatCheckingFuncInfo(
    'numbers-range', is_numbers_range, (TypeError,),
)
