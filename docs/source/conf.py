# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys

DOCS_SOURCE_PATH = pathlib.Path(__file__).parent
assert DOCS_SOURCE_PATH.is_absolute()

PROJECT_ROOT = DOCS_SOURCE_PATH.parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

with open(
    (PROJECT_ROOT / 'jsonschema_extras' / 'VERSION'), 'rt', encoding='utf-8',
) as file:
    version_str = file.readline().strip()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'jsonschema-extras'
copyright = '2026 Viacheslav Syropiatov'
author = 'Viacheslav Syropiatov'
release = version_str

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
    #'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = [
    '**/tests/*',
]


nitpicky = True
nitpick_ignore_regex = [
    ('py:class', r'.*\.GenericAlias'),
    ('py:class', 'D'),
    ('py:.', 'jsonschema_extras.typing.D'),
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']


autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'inherited-members': True,
    'show-inheritance': True,
}
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
