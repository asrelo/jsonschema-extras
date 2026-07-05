from collections.abc import Sequence
from importlib import import_module
from os import PathLike
from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from docs.utils.common.ext import get_current_heading_level
from docs.utils.common.rst import escape_rst
from jsonschema_extras.formats._common import FormatCheckingFuncInfo


def _create_jinja_env(templates_paths: Sequence[str | PathLike[str]]) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_paths),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters['escape_rst'] = escape_rst
    return env


def _get_templates_paths(directive: SphinxDirective) -> list[Path]:
    conf = directive.env.config
    if hasattr(conf, 'jsonschema_format_templates_path'):
        return [(Path(directive.env.srcdir) / conf.jsonschema_format_templates_path)]
    return [(Path(directive.env.srcdir) / '_templates')]


def _get_module_and_attr_path_from_format_info_path(path: str) -> tuple[str, str]:
    parts = path.split('.')
    assert len(parts) >= 1
    if len(parts) < 2:
        raise ValueError(f'Invalid format info object path: {path!r}')
    return ('.'.join(parts[:-1]), parts[-1])


def _import_object(module_path: str, attr_path: str) -> Any:
    obj = import_module(module_path)
    attr_path_parts = attr_path.split('.')
    for attr_path_part in attr_path_parts:
        obj = getattr(obj, attr_path_part)
    return obj


_CANONICAL_FORMATS_PACKAGE_NAME = 'jsonschema_extras.formats'


def _customize_func_module_path(module_path: str) -> str:
    canonical_formats_package_name_split = (
        _CANONICAL_FORMATS_PACKAGE_NAME.split('.')
    )
    module_path_split = module_path.split('.')
    if (
        (len(canonical_formats_package_name_split) <= len(module_path_split))
        and (
            canonical_formats_package_name_split
            == module_path_split[:len(canonical_formats_package_name_split)]
        )
    ):
        module_path_split = canonical_formats_package_name_split
    return '.'.join(module_path_split)


def _build_exception_type_template_context(
    exc_type: type[Exception],
) -> dict[str, Any]:
    exc_type_name = exc_type.__qualname__ or exc_type.__name__
    exc_type_module = exc_type.__module__
    if exc_type_module != 'builtins':
        exc_type_path = '.'.join((exc_type_module, exc_type_name))
    else:
        exc_type_path = exc_type_name
    return {'path': exc_type_path}


def _doc_title_from_format(format: str) -> str:
    return f'``{format}``'


def _build_format_info_template_context(
    format_info: FormatCheckingFuncInfo,
) -> dict[str, Any]:
    func = format_info.func
    func_module_path = func.__module__
    func_module_path = _customize_func_module_path(func_module_path)
    func_name = func.__qualname__ or func.__name__
    func_path = '.'.join((func_module_path, func_name))
    raises = format_info.raises
    if not isinstance(raises, type):
        raises_new = raises
    else:
        raises_new = (raises,)
    exceptions_context = list(map(
        _build_exception_type_template_context, raises_new
    ))
    title = _doc_title_from_format(format_info.format)
    return {
        'title': title,
        'format': format_info.format,
        'func_path': func_path,
        'exception_types': exceptions_context,
    }


class JSONSchemaFormatDirective(SphinxDirective):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {'compact': directives.flag}

    def run(self) -> list[nodes.Node]:
        format_info_path = self.arguments[0].strip()
        try:
            format_info_module_path, format_info_attr_path = (
                _get_module_and_attr_path_from_format_info_path(format_info_path)
            )
        except ValueError as err:
            raise self.error(str(err)) from err
        try:
            format_info = _import_object(
                format_info_module_path, format_info_attr_path,
            )
        except Exception as err:
            return [
                self.state.document.reporter.error(
                    f'Failed to import {format_info_path}: {err}', line=self.lineno,
                )
            ]
        template_context = _build_format_info_template_context(format_info)
        template_context['base_level'] = (
            get_current_heading_level(self.state_machine.node) + 1
        )
        template_context['compact'] = ('compact' in self.options)
        templates_paths = _get_templates_paths(self)
        env = _create_jinja_env(templates_paths)
        try:
            template = env.get_template('formats/format.rst.j2')
            rendered_rst = template.render(**template_context)
        except Exception as err:
            return [
                self.state.document.reporter.error(
                    f'Failed to render Jinja template for {format_info_path}: {err}',
                    line=self.lineno,
                )
            ]
        lines = StringList(rendered_rst.splitlines())
        node = nodes.container()
        self.state.nested_parse(lines, self.content_offset, node, match_titles=True)
        return node.children


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value('jsonschema_format_templates_path', '_templates', 'env')
    app.add_directive('jsonschemaformat', JSONSchemaFormatDirective)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
