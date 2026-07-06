from collections.abc import Callable


__all__ = (
    'LoadTextFn',
)


#: Function to deserialize resource contents.
#:
#: Note:
#:     The function does not produce a resource, it produces resource contents.
#:
#: Args:
#:     str: The raw string content to be deserialized.
#:
#: Returns:
#:     D: The deserialized Python data structure.
type LoadTextFn[D] = Callable[[str], D]
