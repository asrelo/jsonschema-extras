from enum import StrEnum
from pathlib import PurePosixPath
from urllib.parse import SplitResult, unquote, urlsplit


def is_uri_absolute(uri: str | SplitResult) -> bool:
    # here scheme is a default value:
    if not isinstance(uri, SplitResult):
        uri_split = urlsplit(uri, scheme='')
    else:
        uri_split = uri
    return (
        bool(uri_split.scheme)
        or bool(uri_split.netloc)
        or (uri_split.username is not None)
        or (uri_split.password is not None)
    )


class RPURIBValidateURIValueErrorCode(StrEnum):
    IS_RELATIVE = 'is_relative'
    HAS_QUERY = 'has_query'
    HAS_FRAGMENT = 'has_fragment'


class RPURIBValidateURIValueError(ValueError):

    def __init__(self, message: str, code: RPURIBValidateURIValueErrorCode):
        super().__init__(message, code)
        self.code = code


def rpurib_validate_uri_base_split(uri_base_split: SplitResult) -> SplitResult:
    if not is_uri_absolute(uri_base_split):
        raise RPURIBValidateURIValueError(
            'base URI should be absolute',
            RPURIBValidateURIValueErrorCode.IS_RELATIVE,
        )
    if unquote(uri_base_split.query):
        raise RPURIBValidateURIValueError(
            'base URI should not have a query',
            RPURIBValidateURIValueErrorCode.HAS_QUERY,
        )
    if uri_base_split.fragment:
        raise RPURIBValidateURIValueError(
            'base URI should not have a fragment',
            RPURIBValidateURIValueErrorCode.HAS_FRAGMENT,
        )
    return uri_base_split


def rpurib_split_and_validate_uri_base(uri_base: str) -> SplitResult:
    # here scheme is a default value:
    uri_base_split = urlsplit(uri_base, scheme='')
    return rpurib_validate_uri_base_split(uri_base_split)


def rpurib_validate_uri_split(uri_split: SplitResult) -> SplitResult:
    if not is_uri_absolute(uri_split):
        raise RPURIBValidateURIValueError(
            'URI should be absolute',
            RPURIBValidateURIValueErrorCode.IS_RELATIVE,
        )
    if uri_split.fragment:
        raise RPURIBValidateURIValueError(
            'URI should not have a fragment',
            RPURIBValidateURIValueErrorCode.HAS_FRAGMENT,
        )
    if unquote(uri_split.query):
        raise RPURIBValidateURIValueError(
            'URI should not have a query',
            RPURIBValidateURIValueErrorCode.HAS_QUERY,
        )
    return uri_split


def rpurib_split_and_validate_uri(uri: str) -> SplitResult:
    # here scheme is a default value:
    uri_split = urlsplit(uri, scheme='')
    return rpurib_validate_uri_split(uri_split)


class RPURIBNotRelativeValueError(ValueError):
    pass


def relative_path_from_uri_by_base_splits_validated(
    uri_split: SplitResult, uri_base_split: SplitResult,
) -> PurePosixPath:
    uri_path = PurePosixPath(unquote(uri_split.path))
    uri_base_path = PurePosixPath(unquote(uri_base_split.path))
    try:
        return uri_path.relative_to(uri_base_path, walk_up=False)
    except ValueError as err:
        raise RPURIBNotRelativeValueError(str(err)) from err


def _relative_path_from_uri_by_base(
    uri: str | SplitResult, uri_base: str | SplitResult,
) -> PurePosixPath:
    # XXX: ValueError s are propagated
    if not isinstance(uri_base, SplitResult):
        uri_base_split = rpurib_split_and_validate_uri_base(uri_base)
    else:
        uri_base_split = uri_base
    if not isinstance(uri, SplitResult):
        uri_split = rpurib_split_and_validate_uri(uri)
    else:
        uri_split = uri
    return relative_path_from_uri_by_base_splits_validated(uri_split, uri_base_split)


def translate_uri_base_splits_validated(
    uri_split: SplitResult,
    uri_base_old_split: SplitResult,
    uri_base_new_split: SplitResult,
) -> SplitResult:
    path_rel = _relative_path_from_uri_by_base(uri_split, uri_base_old_split)
    uri_base_new_split = rpurib_validate_uri_base_split(uri_base_new_split)
    path_new = PurePosixPath(uri_base_new_split.path) / path_rel
    return uri_split._replace(
        scheme=uri_base_new_split.scheme,
        netloc=uri_base_new_split.netloc,
        path=str(path_new),
    )
