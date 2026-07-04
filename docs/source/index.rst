.. jsonschema-extras documentation master file, created by sphinx-quickstart.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

jsonschema-extras
=================

.. image:: https://img.shields.io/pypi/v/jsonschema-extras.svg
   :target: https://pypi.org/project/jsonschema-extras/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/jsonschema-extras.svg
   :target: https://pypi.org/project/jsonschema-extras/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/asrelo/jsonschema-extras.svg
   :target: https://github.com/asrelo/jsonschema-extras/blob/main/LICENSE.txt
   :alt: License

Utilities for working with the JSON Schema Python library
`jsonschema <https://python-jsonschema.readthedocs.io/>`__.

Features
--------

* :doc:`Schemas bundled with the library <./schemas>`

* :doc:`Formats bundled with the library <./formats>`

* :doc:`Utilities for accessing schemas on a filesystem <./filesystem>`

* :py:class:`~jsonschema_extras.registries.RetrieveFunctionsChain` –
  chain of responsibility composed of retriever functions
  (used to initialize :py:class:`referencing.Registry`).

Installation
------------

Install via pip:

.. code-block:: bash

   pip install jsonschema-extras



.. toctree::
   :maxdepth: 2
   :hidden:

   Home <self>
   filesystem
   schemas
   formats

.. toctree::
   :maxdepth: 2
   :caption: API
   :hidden:

   api/jsonschema_extras
