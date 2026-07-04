Other utilities
===============

* :class:`~jsonschema_extras.registries.RetrieveFunctionsChain` –
  chain of responsibility composed of retriever functions
  (used to initialize :py:class:`referencing.Registry`).

* :func:`~jsonschema_extras.registries.retrieval.to_maybe_cached_resource`
  (also :func:`~jsonschema_extras.registries.retrieval.to_resource`
  and :func:`~jsonschema_extras.registries.retrieval.to_cached_resource`) -
  utility decorators used to make *a callable retrieving text by URI*
  into *a callable retrieving a* :class:`~referencing.Resource` *by URI*,
  with optional caching.
