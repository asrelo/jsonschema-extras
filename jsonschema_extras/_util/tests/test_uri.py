from pathlib import PurePosixPath
from urllib.parse import urlsplit, urlunsplit

import pytest

from jsonschema_extras._util.uri import (
    RPURIBValidateURIValueErrorCode,
    RPURIBValidateURIValueError,
    is_uri_absolute,
    rpurib_validate_uri_base_split,
    rpurib_validate_uri_split,
    RPURIBNotRelativeValueError,
    relative_path_from_uri_by_base_splits_validated,
    translate_uri_base_splits_validated,
)


class TestIsUriAbsolute:

    @pytest.mark.parametrize(
        ('uri', 'is_absolute'),
        [
            ('https://example.com/path?q=1#frag', True),
            ('//example.com/path', True),
            ('mailto:someone@example.com', True),
            ('http://', True),
            ('//user:pass@example.com', True),
            ('/absolute/path', False),
            ('relative/path', False),
            ('../parent', False),
            ('#fragment', False),
            ('?query=val', False),
            ('', False),
        ],
    )
    @staticmethod
    def test_absolute_returns_true(uri, is_absolute):
        assert is_uri_absolute(uri) == is_absolute

    @pytest.mark.parametrize(
        ('uri', 'is_absolute'), [('https://a.b', True), ('/x', False)],
    )
    @staticmethod
    def test_accepts_pre_parsed_split_result(uri, is_absolute):
        assert is_uri_absolute(urlsplit(uri)) == is_absolute


class TestRPURIBValidateURIBaseSplit:

    _VALID_BASE = urlsplit('https://example.com/base')

    @classmethod
    def test_returns_input_for_valid_absolute_base(cls):
        result = rpurib_validate_uri_base_split(cls._VALID_BASE)
        assert result == cls._VALID_BASE

    @pytest.mark.parametrize(
        ('uri_base_split', 'code_exp'),
        [
            (
                _VALID_BASE._replace(scheme='', netloc=''),
                RPURIBValidateURIValueErrorCode.IS_RELATIVE,
            ),
            (
                _VALID_BASE._replace(query='a=1'),
                RPURIBValidateURIValueErrorCode.HAS_QUERY,
            ),
            (
                _VALID_BASE._replace(fragment='section-1'),
                RPURIBValidateURIValueErrorCode.HAS_FRAGMENT,
            ),
        ],
    )
    @staticmethod
    def test_rpurib_validate_uri_base_split_rejects_invalid_base_uris(
        uri_base_split, code_exp,
    ):
        with pytest.raises(RPURIBValidateURIValueError) as exc_info:
            rpurib_validate_uri_base_split(uri_base_split)
        assert exc_info.value.code == code_exp


class TestRPURIBValidateURISplit:

    _VALID_URI = urlsplit('https://example.com/path')

    @classmethod
    def test_returns_input_for_valid_absolute_uri(cls):
        result = rpurib_validate_uri_split(cls._VALID_URI)
        assert result == cls._VALID_URI

    @pytest.mark.parametrize(
        ('uri_split', 'code_exp'),
        [
            (
                _VALID_URI._replace(scheme='', netloc=''),
                RPURIBValidateURIValueErrorCode.IS_RELATIVE,
            ),
            (
                _VALID_URI._replace(query='a=1'),
                RPURIBValidateURIValueErrorCode.HAS_QUERY,
            ),
            (
                _VALID_URI._replace(fragment='section-1'),
                RPURIBValidateURIValueErrorCode.HAS_FRAGMENT,
            ),
        ],
    )
    @staticmethod
    def test_rpurib_validate_uri_split_rejects_invalid_uris(
        uri_split, code_exp,
    ):
        with pytest.raises(RPURIBValidateURIValueError) as exc_info:
            rpurib_validate_uri_split(uri_split)
        assert exc_info.value.code == code_exp


class TestRelativePathFromURIByBaseSplitsValidated:

    @pytest.mark.parametrize(
        ('uri', 'base', 'expected'),
        [
            ('https://ex.com/a/b/c', 'https://ex.com/a/b/', PurePosixPath('c')),
            ('https://ex.com/a/b/c/d', 'https://ex.com/a/b/', PurePosixPath('c/d')),
            ('https://ex.com/a/b', 'https://ex.com/a/b', PurePosixPath('.')),
            ('https://ex.com/a/b/', 'https://ex.com/a/b', PurePosixPath('.')),
            ('https://ex.com/', 'https://ex.com/', PurePosixPath('.')),
            ('https://ex.com/x', 'https://ex.com/', PurePosixPath('x')),
        ],
    )
    @staticmethod
    def test_relative_path_success(uri, base, expected):
        assert (
            relative_path_from_uri_by_base_splits_validated(
                urlsplit(uri), urlsplit(base),
            )
            == expected
        )

    @staticmethod
    def test_raises_not_relative():
        with pytest.raises(RPURIBNotRelativeValueError):
            relative_path_from_uri_by_base_splits_validated(
                urlsplit('https://ex.com/a/b/'), urlsplit('https://ex.com/a/c/d'),
            )


def test_uri_not_under_old_base_propagates_error():
    with pytest.raises(RPURIBNotRelativeValueError):
        translate_uri_base_splits_validated(
            urlsplit('https://old.example.com/other/file'),
            urlsplit('https://old.example.com/base/'),
            urlsplit('https://new.example.com/base/'),
        )


@pytest.mark.parametrize(
    ('uri', 'old_base', 'new_base', 'expected'),
    [
        (
            'https://old.example.com/base/file.txt',
            'https://old.example.com/base/',
            'https://new.example.com/newbase/',
            'https://new.example.com/newbase/file.txt',
        ),
        (
            'https://old.example.com/base/sub/deep/file.txt',
            'https://old.example.com/base/',
            'https://new.example.com/newbase/',
            'https://new.example.com/newbase/sub/deep/file.txt',
        ),
        (
            'https://old.example.com/base/file',
            'https://old.example.com/base/',
            'http://new.example.com/base/',
            'http://new.example.com/base/file',
        ),
        (
            'https://old.example.com/base/file',
            'https://old.example.com/base/',
            'https://new-domain.com/base/',
            'https://new-domain.com/base/file',
        ),
        (
            'https://old.example.com/base/file',
            'https://old.example.com/base/',
            'https://user:pass@new.example.com/base/',
            'https://user:pass@new.example.com/base/file',
        ),
        (
            'https://old.example.com/base/file',
            'https://old.example.com/base/',
            'https://new.example.com:8080/base/',
            'https://new.example.com:8080/base/file',
        ),
        (
            'https://old.example.com/base/file',
            'https://old.example.com/base/',
            'https://new.example.com/a/b/c/base/',
            'https://new.example.com/a/b/c/base/file',
        ),
    ],
)
def test_translation_uri_base_splits_validated(uri, old_base, new_base, expected):
    assert (
        urlunsplit(translate_uri_base_splits_validated(
            urlsplit(uri), urlsplit(old_base), urlsplit(new_base),
        ))
        == expected
    )
