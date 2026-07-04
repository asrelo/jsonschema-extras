import json
from typing import Any, Final

from jsonschema_extras._common import Kwargs
from ._common import LoadTextFn


def schema_data_from_json_text(text: str, *, loads_kwargs: Kwargs | None = None) -> Any:
    '''Deserialize a schema from JSON text

    Satisfies :type:`.LoadTextFn`.'''
    if loads_kwargs is None:
        loads_kwargs = {}
    return json.loads(text, **loads_kwargs)


LOADS_FN_JSON_DEFAULT: Final[LoadTextFn[Any]] = schema_data_from_json_text
