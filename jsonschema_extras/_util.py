from collections.abc import Collection, Hashable, Mapping
from typing import TypeVar


_K = TypeVar('_K', bound=Hashable)
_V = TypeVar('_V')


COLLECTION_PRIMITIVE_TYPES_DEFAULT: Collection[type] = (str, bytes, bytearray, memoryview)

SEQUENCE_PRIMITIVE_TYPES_DEFAULT: Collection[type] = (*COLLECTION_PRIMITIVE_TYPES_DEFAULT,)


def coerce_to_dict(mapping: Mapping[_K, _V]) -> dict[_K, _V]:
    if isinstance(mapping, dict):
        return mapping
    return dict(mapping.items())
