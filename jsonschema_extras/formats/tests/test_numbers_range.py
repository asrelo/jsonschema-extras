import pytest

from jsonschema_extras.formats.numbers_range import is_numbers_range


@pytest.mark.parametrize(
    ('value, expected'),
    [
        ((0, 1), True),
        ((-5, -5), True),
        ((3.14, 9.81), True),
        ((10, 2), False),
        ((1,), False),
        ((1, 2, 3), False),
        (5, False),
        (None, False),
        ('ab', False),
        (b'', False),
    ],
)
def test_is_numbers_range(value, expected):
    assert is_numbers_range(value) == expected
