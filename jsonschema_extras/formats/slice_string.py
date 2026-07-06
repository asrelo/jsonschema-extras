import re

from ._common import FormatCheckingFuncInfo


SLICE_STRING_PATTERN = re.compile(
    r'^'
    r'(?P<start>(?:\-)?\d+)?'
    r':(?P<stop>(?:\-)?\d+)?'
    r'(?::(?P<step>(?:\-)?\d+))?'
    r'$',
)


def is_slice_string(instance: object) -> bool:
    if not isinstance(instance, str):
        raise TypeError(f'str expected, got {type(instance)!r}')
    return (SLICE_STRING_PATTERN.match(instance) is not None)


is_slice_string_info = FormatCheckingFuncInfo(
    'slice-string', is_slice_string, (TypeError, ValueError),
)
