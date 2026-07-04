Accessing schemas on\ |nbsp|\ a\ |nbsp|\ filesystem
===================================================

Overview
--------

The :py:mod:`jsonschema_extras.registries.filesystem` module provides utilities
for accessing schemas on a filesystem directory structure
while supporting references by URIs.

Key concepts
------------

The core concept is a mapping between:

- a **base URI** (e.g., ``file:/schemas/``) that serves as the root identifier
- a **filesystem path** (e.g., ``/var/lib/schemas/``) that contains
  the actual schema files

When a schema URI like ``file:/schemas/person.json`` is requested, the module:

1. Strips the base URI portion (``file:/schemas/``).
2. Uses the remainder (``person.json``) as a relative path.
3. Resolves it against the filesystem root (``/var/lib/schemas/person.json``).
4. Loads and returns the schema from that file.

URIs are **restricted**:

- URIs must contain only a scheme and a path component;
  **no** credentials, network locations, query strings, or fragments allowed;
- **only** ``file:`` scheme URIs are permitted;
- **no** parent directory segments (``..``) in paths (to prevent filesystem
  traversal attacks).

These restrictions are validated automatically by the module's functions.

Basic usage
-----------

**Simple schema retrieval**

.. code-block:: python

    from jsonschema_extras.registries.filesystem import (
        build_schemas_from_filesystem_retriever,
    )

    retrieve = build_schemas_from_filesystem_retriever(
        'file:/schemas/', '/var/lib/schemas/',
    )

    schema = retrieve('file:/schemas/user.json').contents

**With resource caching**

.. code-block:: python

    from jsonschema_extras.registries.filesystem import (
        build_schemas_from_filesystem_retriever,
    )

    retrieve = build_schemas_from_filesystem_retriever(
        'file:/schemas/',
        '/var/lib/schemas/',
        cache='default',    # use built-in caching
    )

    resource1 = retrieve('file:///schemas/user.json')
    # second call uses the cached resource:
    resource2 = retrieve("file:///schemas/user.json")
    assert resource2 is resource 2

Using ``referencing``
----------------------------

Using cross-schema references
with `referencing <https://referencing.readthedocs.io/>`__.

.. code-block:: python

    from jsonschema import validate
    from jsonschema_extras.registries.filesystem import (
        build_schemas_from_filesystem_retriever,
    )
    from referencing import Registry

    retrieve = build_schemas_from_filesystem_retriever(
        'file:/schemas/', '/var/lib/schemas/', cache='default',
    )

    registry = Registry(retrieve=retrieve)

    main_schema = {
        '$id': 'file:///schemas/order.json',
        '$ref': 'file:///schemas/customer.json',
    }

    data = { 'customer_id': 123, 'items': [] }
    # referenced schema is used automatically:
    validate(data, main_schema, registry=registry)

Advanced usage
--------------

Schema files are assumed to be written in JSON by default,
but the :py:func:`~jsonschema_extras.registries.filesystem.build_schemas_from_filesystem_retriever`
function takes the argument `loads` which can be used to replace
the deserialization code.

For multiple schema roots,
you can use :py:class:`jsonschema_extras.registries.RetrieveFunctionsChain`:

.. code-block:: python

    from jsonschema_extras.registries import RetrieveFunctionsChain
    from jsonschema_extras.registries.filesystem import (
        build_schemas_from_filesystem_retriever,
    )
    from referencing import Registry

    public_retriever = build_schemas_from_filesystem_retriever(
        'file:/public/', '/var/lib/public-schemas/', cache='default',
    )
    internal_retriever = build_schemas_from_filesystem_retriever(
        'file:/internal/', '/var/lib/internal-schemas/', cache='default'
    )

    registry = Registry(
        retrieve=RetrieveFunctionsChain(internal_retriever, public_retriever),
    )
