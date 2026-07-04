# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from collections.abc import Iterator
from csv import reader
import pathlib
import sys


DOCS_SOURCE_PATH = pathlib.Path(__file__).parent
assert DOCS_SOURCE_PATH.is_absolute()
sys.path.insert(0, str(DOCS_SOURCE_PATH))

PROJECT_ROOT = DOCS_SOURCE_PATH.parents[1]

sys.path.insert(0, str(PROJECT_ROOT))


def _read_version_from_file(file):
    return file.readline().strip()

def _open_version_file(path):
    return open(path, 'rt', encoding='utf-8')

def _read_version_from_path(path):
    with _open_version_file(path) as file:
        return _read_version_from_file(file)


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'jsonschema-extras'
copyright = '2026 Viacheslav Syropiatov'
author = 'Viacheslav Syropiatov'
release = _read_version_from_path(PROJECT_ROOT / 'jsonschema_extras' / 'VERSION')

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    #'sphinx.ext.autosummary',
    #'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = [
    '**/tests/*',
]


rst_prolog = '''
.. include:: /global.rst
'''


def _read_nitpick_ignore_regex_pairs_it_from_reader(reader):
    for row in reader:
        if ((len(row) == 1) and row[0].startswith('#')) or (len(row) != 2):
            continue
        yield tuple(row)

def _read_nitpick_ignore_regex_from_file(file):
    return list(_read_nitpick_ignore_regex_pairs_it_from_reader(reader(file)))

def _open_nitpick_ignore_regex_file(path):
    return open(path, 'rt', encoding='utf-8', newline='')

def _read_nitpick_ignore_regex_from_path(path):
    with _open_nitpick_ignore_regex_file(path) as file:
        return _read_nitpick_ignore_regex_from_file(file)


nitpicky = True
nitpick_ignore_regex = [
    ('py:class', r'.*\.GenericAlias'),
    *_read_nitpick_ignore_regex_from_path(
        DOCS_SOURCE_PATH / 'nitpick_ignore_regex.csv'
    ),
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']


def _read_alias_pairs_it_from_file(file) -> Iterator[tuple[str, str]]:
    for line in file:
        line_strip = line.strip()
        if (len(line_strip) == 0) or line_strip.startswith('#'):
            continue
        line_split = line_strip.split(':', 1)
        assert len(line_split) <= 2
        if len(line_split) < 2:
            continue    # XXX: ...
        yield tuple(e.strip() for e in line_split)

def _read_aliases_from_file(file):
    return dict(_read_alias_pairs_it_from_file(file))   # XXX: ...

def _open_aliases_file(path):
    return open(path, 'rt', encoding='utf-8')

def _read_aliases_from_path(path):
    with _open_aliases_file(path) as file:
        return _read_aliases_from_file(file)

def _read_aliases_from_path_optional(path):
    try:
        return _read_aliases_from_path(path)
    except FileNotFoundError:
        return {}


TYPE_ALIASES = _read_aliases_from_path_optional(
    DOCS_SOURCE_PATH / 'autodoc_type_aliases.txt'
)

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    #'inherited-members': True,
    'show-inheritance': True,
}
autodoc_type_aliases = TYPE_ALIASES
autodoc_typehints = 'description'

apidoc_separate_modules = True
apidoc_module_first = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/', None),
    'jsonschema': ('https://python-jsonschema.readthedocs.io/en/stable/', None),
    'referencing': ('https://referencing.readthedocs.io/en/stable/', None),
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

copybutton_prompt_text = r'>>> |\.\.\. |\$'
copybutton_prompt_is_regexp = True


def skip_namedtuple_attributes(app, obj_type, name, obj, skip, options):
    # NamedTuple fields are non-callable descriptors that aren't properties
    if (
        (obj_type == 'class')
        and hasattr(obj, '__get__')
        and (not isinstance(obj, property))
        and (not callable(obj))
    ):
        return True
    return skip


def setup(app):
    # XXX: Move to a custom extension at `docs/_ext/...`?
    #   Remember to return a metadata dict then.
    app.connect('autodoc-skip-member', skip_namedtuple_attributes)
