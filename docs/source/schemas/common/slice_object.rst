Slice object
============

**ID:** ``file:/jsonschema_extras/schemas/common/slice_object.json``

Represents a slice notation for selecting a range of elements, similar to Python's slice(start, stop, step) syntax. All properties are optional.

Examples
--------

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
