Other utilities
===============

* :class:`~jsonschema_extras.registries.RetrieversChain` –
  chain of responsibility composed of retriever functions
  (used to initialize :py:class:`referencing.Registry`).

* :class:`~jsonschema_extras.registries.RetrievalURITranslator` –
  decorator for a :class:`~referencing.typing.Retrieve` callable
  translating URIs that match with a given old base URI to a new base URI.

* :func:`~jsonschema_extras.registries.retrieval.to_maybe_cached_resource`
  (also :func:`~jsonschema_extras.registries.retrieval.to_resource`
  and :func:`~jsonschema_extras.registries.retrieval.to_cached_resource`) -
  utility decorators used to make *a callable retrieving text by URI*
  into *a callable retrieving a* :class:`~referencing.Resource` *by URI*,
  with optional caching.
