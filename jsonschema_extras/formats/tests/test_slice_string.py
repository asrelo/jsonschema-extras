import pytest

from jsonschema_extras.formats.slice_string import is_slice_string


class TestIsSliceString:

    @pytest.mark.parametrize(
        ('value, expected'),
        [
            (':', True),
            ('1:5', True),
            (':-2', True),
            ('-3:', True),
            ('::2', True),
            ('0:10:2', True),
            ('-5:-1', True),
            ('-5:-1:-2', True),
            ('-5:10:-2', True),
            ('', False),
            ('123', False),
            ('1,2', False),
            ('1:2:3:4', False),
            ('1::', False),
            ('a:b', False),
            ('1:b', False),
            (' 1:2', False),
            ('1:2 ', False),
        ],
    )
    @staticmethod
    def test_str(value, expected):
        assert is_slice_string(value) == expected

    @pytest.mark.parametrize('value', [123, 3.14, None, [], {}, b'1:2'])
    @staticmethod
    def test_non_str(value):
        with pytest.raises(TypeError):
            is_slice_string(value)
