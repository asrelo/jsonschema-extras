"""Utilities for working with format checkers, and some bundled
format checkers.

To use some of the bundled format checkers:

1. instantiate a :class:`jsonschema.FormatChecker`
   (or use one which you already instantiate);
2. add desired format checking functions to the format checker
   using :func:`register_funcs_in_checker` or :func:`register_func_in_checker`
   with bundled instances of :class:`FormatCheckingFuncInfo`;
3. pass the format checker to :func:`jsonschema.validate`
   or :class:`jsonschema.protocols.Validator` to enable validation of formats.
"""

from ._common import *  # noqa: F401,F403
from .numbers_range import *  # noqa: F401,F403
from .slice_string import *  # noqa: F401,F403


__all__ = (
    'FormatCheckFn',
    'FormatCheckingFuncInfo',
    'register_func_in_checker',
    'register_funcs_in_checker',
    'is_numbers_range',
    'is_numbers_range_info',
    'SLICE_STRING_PATTERN',
    'is_slice_string',
    'is_slice_string_info',
)
