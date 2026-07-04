import re


_INLINE_CHAR_PATTERN = re.compile(r'[*`|]')

_DIRECTIVE_START_PATTERN = re.compile(r'(:)(?=[:\s]|$)')

_LINK_END_PATTERN = re.compile(r'(_)(?=\s|\b|$)')


def escape_rst(text: str) -> str:
    text = text.replace('\\', '\\\\')
    text = _INLINE_CHAR_PATTERN.sub(r'\\\0', text)
    text = _DIRECTIVE_START_PATTERN.sub(r'\\\1', text)
    text = _LINK_END_PATTERN.sub(r'\\\1', text)
    return text
