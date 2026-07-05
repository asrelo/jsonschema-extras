:tocdepth: 2

Bundled schemas
===============


``common/range``: Numbers range
-------------------------------

**ID:** ``file:/jsonschema_extras/schemas/common/range.json``

Represents a numeric range defined by a minimum and maximum value. The array must contain exactly two numbers where the first element is the lower bound and the second is the upper bound.



``common/range_integer``: Integer range
---------------------------------------

**ID:** ``file:/jsonschema_extras/schemas/common/range_integer.json``

A range defined by minimum and maximum integer boundaries

Examples
^^^^^^^^

.. dropdown:: Examples

   .. code-block:: json

      [
        0,
        100
      ]

   .. code-block:: json

      [
        -50,
        50
      ]

   .. code-block:: json

      [
        1,
        1000
      ]



``common/slice_object``: Slice object
-------------------------------------

**ID:** ``file:/jsonschema_extras/schemas/common/slice_object.json``

Represents a slice notation for selecting a range of elements, similar to Python's slice(start, stop, step) syntax. All properties are optional.

Examples
^^^^^^^^

.. dropdown:: Examples

   .. code-block:: json

      {
        "start": 0,
        "stop": 10,
        "step": 1
      }

   .. code-block:: json

      {
        "start": 5,
        "stop": 15
      }

   .. code-block:: json

      {
        "start": 0,
        "step": 2
      }

   .. code-block:: json

      {
        "stop": 10
      }



``common/slice_string``: Slice string
-------------------------------------

**ID:** ``file:/jsonschema_extras/schemas/common/slice_string.json``

A string representing a slice operation in Python notation. Supports start:stop:step syntax where each component is optional and can be negative. Used for specifying ranges and steps in sequence operations.

Examples
^^^^^^^^

.. dropdown:: Examples

   .. code-block:: json

      "1:10"

   .. code-block:: json

      ":10"

   .. code-block:: json

      "1:"

   .. code-block:: json

      "::2"

   .. code-block:: json

      "1:10:2"

   .. code-block:: json

      "-5:"

   .. code-block:: json

      ":-5"

   .. code-block:: json

      "0:100:5"

   .. code-block:: json

      "-10:-2:1"
