# TODO: use something like "fractured JSON" for examples (pretty but fairly compact)

from collections.abc import Sequence
import json
from os import PathLike
from pathlib import Path
from typing import Any, Final

from docutils import nodes
from docutils.statemachine import StringList
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from docs.utils.common.rst import escape_rst


logger: Final = logging.getLogger(__name__)


TITLE_FALLBACK_NONE: Final = '(unknown)'


def jinja_filter_to_pretty_json(obj: Any, indent: int = 2) -> str:
    return json.dumps(obj, indent=indent, ensure_ascii=False)


def _create_jinja_env(templates_paths: Sequence[str | PathLike[str]]) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_paths),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters['escape_rst'] = escape_rst
    env.filters['to_pretty_json'] = jinja_filter_to_pretty_json
    return env


def _get_templates_paths(directive: SphinxDirective) -> list[Path]:
    conf = directive.env.config
    if hasattr(conf, 'jsonschema_templates_path'):
        return [(Path(directive.env.srcdir) / conf.jsonschema_templates_path)]
    return [(Path(directive.env.srcdir) / '_templates')]


def _read_schema_from_path(path: Path) -> dict[str, Any]:
    with open(path, 'rt', encoding='utf-8') as file:
        return json.load(file)


def _doc_title_from_filename(name: str) -> str:
    return Path(name).stem.replace('_', ' ').title()


def _doc_title_for_multi_page(doc_name: str, title: str) -> str:
    return f'``{doc_name}``: {title}'


def _build_template_params(
    schema: dict[str, Any], *, title_fallback: str | None = None,
) -> tuple[dict[str, Any], str]:
    if title_fallback is None:
        title_fallback = TITLE_FALLBACK_NONE
    title = schema.get('title', title_fallback)
    params = {
        'schema': schema,
        'title': title,
        'schema_id': schema.get('$id'),
        'schema_uri': schema.get('$schema'),
    }
    return (params, title)


class JSONSchemaDirective(SphinxDirective):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self) -> list[nodes.Node]:
        rel_fn, abs_fn = self.env.relfn2path(self.arguments[0])
        self.env.note_dependency(rel_fn)
        schema_path = Path(abs_fn)
        try:
            schema = _read_schema_from_path(schema_path)
        except FileNotFoundError:
            return [
                self.state.document.reporter.error(
                    f'JSON schema file not found: {schema_path}', line=self.lineno,
                )
            ]
        except Exception as err:
            return [
                self.state.document.reporter.error(
                    f'Failed to read/parse schema {schema_path}: {err}',
                    line=self.lineno,
                )
            ]
        templates_paths = _get_templates_paths(self)
        env = _create_jinja_env(templates_paths)
        title_fallback = _doc_title_from_filename(schema_path.name)
        params, _ = _build_template_params(schema, title_fallback=title_fallback)
        try:
            template = env.get_template('schemas/schema.rst.j2')
            rendered_rst = template.render(**params)
        except Exception as err:
            return [
                self.state.document.reporter.error(
                    f'Failed to render Jinja template for {schema_path.name}: {err}',
                    line=self.lineno,
                )
            ]
        nested_rules = nodes.container()
        lines = StringList(rendered_rst.splitlines())
        self.state.nested_parse(lines, self.content_offset, nested_rules)
        return nested_rules.children


class JSONSchemasDirDirective(SphinxDirective):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self) -> list[nodes.Node]:  # noqa: C901
        _, abs_dir = self.env.relfn2path(self.arguments[0])
        schemas_path = Path(abs_dir)
        if not schemas_path.is_dir():
            return [
                self.state.document.reporter.warning(
                    f'Schemas directory not found: {schemas_path}', line=self.lineno,
                ),
            ]
        schema_files = sorted(schemas_path.rglob('*.json'))
        if not schema_files:
            return [
                self.state.document.reporter.warning(
                    f'No JSON schema files found in {schemas_path}.', line=self.lineno,
                )
            ]
        result_nodes: list[nodes.Node] = []
        schema_entries = []
        for path in schema_files:
            try:
                rel_to_src = path.relative_to(self.env.srcdir)
            except ValueError:
                logger.debug(
                    f'Schema {path} is outside source directory,'
                    f' changes will not trigger rebuild',
                )
            else:
                self.env.note_dependency(str(rel_to_src))
            try:
                schema = _read_schema_from_path(path)
                schema_rel = path.relative_to(schemas_path)
                info = {
                    'title_fallback': _doc_title_from_filename(schema_rel.name),
                    'doc_name': schema_rel.with_suffix('').as_posix(),
                }
                schema_entries.append((schema, info))
            except Exception as err:
                logger.error(f'Failed to process schema {path.name}: {err}')
                result_nodes.append(
                    self.state.document.reporter.warning(
                        f'Failed to process schema {path.name}: {err}',
                        line=self.lineno
                    )
                )
        templates_paths = _get_templates_paths(self)
        env = _create_jinja_env(templates_paths)
        try:
            template = env.get_template('schemas/schema.rst.j2')
        except Exception as err:
            return [
                self.state.document.reporter.error(
                    f'Failed to load template: {err}', line=self.lineno,
                )
            ]
        rendered_parts = []
        for schema, info in schema_entries:
            params, title_tmp = _build_template_params(
                schema, title_fallback=info['title_fallback'],
            )
            doc_name = info.get('doc_name')
            if doc_name is None:
                doc_name = title_tmp
            params['title'] = _doc_title_for_multi_page(doc_name, params['title'])
            params['compact'] = True
            params['base_level'] = 2
            try:
                rendered_rst = template.render(**params)
                rendered_parts.append(rendered_rst)
            except Exception as err:
                logger.error(
                    f'Failed to render schema {info['title_fallback']}: {err}'
                )
                result_nodes.append(
                    self.state.document.reporter.warning(
                        f'Failed to render schema {info['title_fallback']}: {err}',
                        line=self.lineno
                    )
                )
        rendered_rst = '\n\n'.join([*rendered_parts, ''])   # XXX: ?
        lines = StringList(rendered_rst.splitlines())
        nested_rules = nodes.container()
        self.state.nested_parse(
            lines, self.content_offset, nested_rules, match_titles=True,    # XXX: ?
        )
        result_nodes.extend(nested_rules.children)
        return result_nodes


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value('jsonschema_templates_path', '_templates', 'env')
    app.add_directive('jsonschema', JSONSchemaDirective)
    app.add_directive('jsonschemas', JSONSchemasDirDirective)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
