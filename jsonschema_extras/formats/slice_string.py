import re

from ._common import FormatCheckingFuncInfo


#: Compiled regex pattern for a slice string.
#:
#: Matches Python's :class:`slice` syntax in string form: ``start:stop:step``
#: where all components are optional integers (may be negative).
SLICE_STRING_PATTERN = re.compile(
    r'^'
    r'(?P<start>(?:\-)?\d+)?'
    r':(?P<stop>(?:\-)?\d+)?'
    r'(?::(?P<step>(?:\-)?\d+))?'
    r'$',
)


def is_slice_string(instance: object) -> bool:
    """Tests if a string specifies a slice.

    A slice string follows Python's :class:`slice` syntax: ``start:stop:step``
    where ``start``, ``stop``, and ``step`` are optional integers
    that may be negative. At minimum, the string must contain
    at least one colon.

    Returns:
        Whether the string is a slice string
        (by the Python's :class:`slice` syntax).

    Raises:
        TypeError: If the given object is not a string.

    Examples:

        Valid slice strings::

            >>> is_slice_string('1:5')
            True
            >>> is_slice_string('::2')
            True
            >>> is_slice_string('-5:')
            True
            >>> is_slice_string(':')
            True

        Invalid slice strings::

            >>> is_slice_string('1.5:10')
            False
            >>> is_slice_string('a:b')
            False

        Type checking::

            >>> is_slice_string(123)
            Traceback (most recent call last):
                ...
            TypeError: str expected, got <class 'int'>
    """
    if not isinstance(instance, str):
        raise TypeError(f'str expected, got {type(instance)!r}')
    return (SLICE_STRING_PATTERN.match(instance) is not None)


#: Format ``slice-string`` checked by :func:`is_slice_string_info`
is_slice_string_info = FormatCheckingFuncInfo(
    'slice-string', is_slice_string, (TypeError, ValueError),
)
