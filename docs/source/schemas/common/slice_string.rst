Slice string
============

**ID:** ``file:/jsonschema_extras/schemas/common/slice_string.json``

A string representing a slice operation in Python notation. Supports start:stop:step syntax where each component is optional and can be negative. Used for specifying ranges and steps in sequence operations.

Examples
--------

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
