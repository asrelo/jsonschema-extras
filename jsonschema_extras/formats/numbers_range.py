from collections.abc import Sequence

from jsonschema_extras._util import SEQUENCE_PRIMITIVE_TYPES_DEFAULT
from ._common import FormatCheckingFuncInfo


def is_numbers_range(instance: object) -> bool:
    return (
        isinstance(instance, Sequence)
        and (not isinstance(instance, tuple(SEQUENCE_PRIMITIVE_TYPES_DEFAULT)))
        and (len(instance) == 2)
        and (instance[0] <= instance[1])
    )

is_numbers_range_info = FormatCheckingFuncInfo('numbers-range', is_numbers_range, (TypeError,))
