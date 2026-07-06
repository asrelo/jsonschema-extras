from pathlib import PurePath
from urllib.parse import SplitResult

import pytest

from jsonschema_extras.registries.filesystem import (
    split_and_validate_uri_base,
    NoSuchResourceFromValueError,
    split_and_validate_uri,
    file_path_from_uri_by_base,
)


class TestSplitAndValidateUriBase:

    @staticmethod
    def test_valid_file_uri_returns_split_result():
        result = split_and_validate_uri_base('file:/absolute/path/to/file')
        assert isinstance(result, SplitResult)
        assert result.scheme == 'file'
        assert result.path == '/absolute/path/to/file'

    @pytest.mark.parametrize(
        'invalid_uri',
        [
            'http://example.com',
            'https:///path',
            '',
            'file://localhost/path',
            'file://host.com/path',
            'file://user@host/path',
            'file://:password@host/path',
            'file:/path?query=value',
            'file:path?query%3Dvalue',
            'file:/path?key=val',
            'file:path#section',
            'file:/path#anchor',
        ],
    )
    @staticmethod
    def test_invalid_uri_raises_value_error(invalid_uri):
        with pytest.raises(ValueError):
            split_and_validate_uri_base(invalid_uri)


class TestSplitAndValidateUri:

    @staticmethod
    def test_valid_file_uri_returns_split_result():
        result = split_and_validate_uri('file:/absolute/path/to/file')
        assert isinstance(result, SplitResult)
        assert result.scheme == 'file'
        assert result.path == '/absolute/path/to/file'

    @pytest.mark.parametrize(
        'invalid_uri',
        [
            'http://example.com',
            'https:///path',
            '',
            'file://localhost/path',
            'file://host.com/path',
            'file://user@host/path',
            'file://:password@host/path',
            'file:path#section',
            'file:/path#anchor',
        ],
    )
    @staticmethod
    def test_invalid_uri_raises_value_error(invalid_uri):
        with pytest.raises(ValueError):
            split_and_validate_uri(invalid_uri)

    @pytest.mark.parametrize(
        'invalid_uri', ['file:/path?query=value', 'file:path?query%3Dvalue', 'file:/path?key=val'],
    )
    @staticmethod
    def test_invalid_uri_raises_no_such_resource_from_value_error(invalid_uri):
        with pytest.raises(NoSuchResourceFromValueError):
            split_and_validate_uri(invalid_uri)


class TestFilePathFromUriByBase:

    @pytest.mark.parametrize(
        ('uri', 'uri_base', 'path', 'result'),
        [
            (
                'file:/server/share/file.txt', 'file:/server/share/', '/local/base',
                '/local/base/file.txt',
            ),
            ('file:/server/share/file.txt', 'file:/server/share', '/base', '/base/file.txt'),
            (
                'file:/server/share/dir/file.txt', 'file:/server/share', '/base',
                '/base/dir/file.txt',
            ),
            (
                'file:/server/share/a/b/c/file.txt', 'file:/server/share', '/base',
                '/base/a/b/c/file.txt',
            ),
            (
                'file:/server/share/file%20name%2Bversion.txt', 'file:/server/share/', '/base',
                '/base/file name+version.txt',
            ),
            (
                'file:/server/share/file.txt', 'file:/server/share/', 'relative/base',
                'relative/base/file.txt',
            ),
        ],
    )
    @staticmethod
    def test_main(uri, uri_base, path, result):
        assert file_path_from_uri_by_base(uri, uri_base, path) == PurePath(result)

    @pytest.mark.parametrize(
        ('uri', 'uri_base', 'path'),
        [
            ('file:/other/path/file.txt', 'file:/server/share/', '/base'),
            ('file:/server/file.txt', 'file:/server/share/', '/base'),
        ],
    )
    @staticmethod
    def test_non_relative_uri_raises_error(uri, uri_base, path):
        with pytest.raises(NoSuchResourceFromValueError):
            file_path_from_uri_by_base(uri, uri_base, path)
