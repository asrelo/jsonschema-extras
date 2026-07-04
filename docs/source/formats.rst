Formats
=======

To enable format validation with bundled format checkers:

1. Create an instance of :py:class:`jsonschema.FormatChecker`,
   or use an existing format checker instance.
2. Register the desired format checking functions to the format checker using
   :py:func:`~jsonschema_extras.formats.register_funcs_in_checker`
   or :py:func:`~jsonschema_extras.formats.register_func_in_checker`
   with bundled :py:class:`~jsonschema_extras.formats.FormatCheckingFuncInfo`
   instances.
3. Pass the format checker to :py:func:`jsonschema.validate`
   or to your :py:class:`jsonschema.protocols.Validator` instance to enable
   format validation

**Basic example:**

.. code-block:: python

    from typing import Any

    from jsonschema import FormatChecker, validate
    from jsonschema_extras.formats import (
        register_funcs_in_checker,
        is_numbers_range_info,
        is_slice_string_info,
    )

    schema: Any
    instance: Any

    format_checker = FormatChecker()
    register_funcs_in_checker(
        format_checker, [is_numbers_range_info, is_slice_string_info],
    )
    validate(instance, schema, format_checker=format_checker)
