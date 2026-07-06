from collections.abc import Collection, Mapping
from typing import Any, TypeAlias


__all__ = ()


type Kwargs = Mapping[str, Any]


# NOTE: returns kwargs without changes
def validate_kwargs(
    kwargs: Kwargs, *, allowed: Collection[str] = (), required: Collection[str] = (),
) -> Kwargs:
    # NOTE: using lists instead of sets to preserve order
    allowed = list(allowed)
    allowed += [s for s in required if s not in allowed]
    unexpected = [s for s in kwargs if s not in allowed]
    if len(unexpected) > 0:
        raise TypeError('got unexpected keyword argument(s): {0}'.format(', '.join(unexpected)))
    missing = [s for s in required if s not in kwargs]
    if len(missing) > 0:
        raise TypeError('missing required keyword argument(s): {0}'.format(', '.join(missing)))
    return kwargs


EncodingId: TypeAlias = str
