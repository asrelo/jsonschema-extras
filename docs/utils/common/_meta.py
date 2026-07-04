from pathlib import Path


PACKAGE_PATH = Path(__file__).parent
assert PACKAGE_PATH.is_absolute()

DOCS_UTILS_PATH = PACKAGE_PATH.parents[0]

DOCS_PATH = DOCS_UTILS_PATH.parents[0]

PROJECT_PATH = DOCS_PATH.parents[0]

DOCS_SOURCE_PATH = DOCS_PATH / 'source'

DOCS_TEMPLATES_PATH = DOCS_SOURCE_PATH / '_templates'
