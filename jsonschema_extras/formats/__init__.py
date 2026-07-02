'''Utilities for working with format checkers, and some bundled
format checkers.

To use some of the bundled format checkers:

1. instantiate a :class:`jsonschema.FormatChecker`
   (or use one which you already instantiate);
2. add desired format checking functions to the format checker
   using :func:`~._common.register_funcs_in_checker`
   or :func:`~._common.register_func_in_checker` with bundled instances
   of :class:`~._common.FormatCheckingFuncInfo`;
3. pass the format checker to :func:`jsonschema.validate`
   or :class:`jsonschema.Validator` to enable validation of formats.
'''

from ._common import *  # noqa: F401,F403
from .numbers_range import *  # noqa: F401,F403
from .slice_string import *   # noqa: F401,F403
