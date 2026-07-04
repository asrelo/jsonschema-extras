Schemas
=======

:doc:`List of bundled schemas <./schemas/index>`

To access bundled schemas within your project:

1. Create a retrieval callable using
   :py:func:`~jsonschema_extras.bundled_schemas_retriever`.
2. Pass this callable when instantiating :py:class:`referencing.Registry`

All bundled schemas will be available through the registry, using the base URI
you specified in :py:func:`~jsonschema_extras.bundled_schemas_retriever`.
If no URI is provided,
it defaults to :py:data:`~jsonschema_extras.BUNDLED_SCHEMAS_URI_BASE_DEFAULT`.

**Basic example:**

.. code-block:: python

    from typing import Any

    from jsonschema import Validator
    from jsonschema_extras import bundled_schemas_retriever
    from referencing import Registry

    your_schema: Any

    with bundled_schemas_retriever() as retrieve:
        registry = Registry(retrieve=retrieve)
        validator = Validator(your_schema, registry=registry)
        # use validator

**Chaining multiple retrievers:**

Use :py:class:`~jsonschema_extras.registries.RetrieveFunctionsChain`
to combine multiple retrieval callables.

.. code-block:: python

    from jsonschema_extras import RetrieveFunctionsChain, bundled_schemas_retriever
    from referencing import Registry
    from referencing.typing import Retrieve

    retrieve_custom: Retrieve

    with bundled_schemas_retriever() as retrieve_bundled_schemas:
        registry = Registry(
            retrieve=RetrieveFunctionsChain(
                retrieve_custom, retrieve_bundled_schemas,
            ),
        )
        validator = Validator(your_schema, registry=registry)
        # use validator

.. toctree::
   :maxdepth: 1
   :hidden:

   schemas/index
