# TODO: use something like "fractured JSON" for examples (pretty but fairly compact)

from argparse import ArgumentParser
from collections.abc import Sequence
from enum import StrEnum
import json
from pathlib import PurePosixPath, PurePath, Path
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

from docs.utils.common import purge_directory

from .common._meta import PROJECT_PATH, DOCS_SOURCE_PATH, DOCS_TEMPLATES_PATH
from .common.rst import escape_rst


SCRIPT_IDENTITY = 'generate_schema'


class LayoutMode(StrEnum):
    SINGLE = 'single'
    MULTI = 'multi'


LAYOUT_MODE_DEFAULT = LayoutMode.SINGLE


SCHEMAS_REL_PATH_DEFAULT = PurePath('jsonschema_extras') / 'schemas'

OUTPUT_SOURCE_REL_PATH_DEFAULT = PurePath('schemas')

INDEX_DOC_NAME_DEFAULT = PurePosixPath('index')


TITLE_FALLBACK_NONE = '(unknown)'


def _print_err(*values: object, file=None, **kwargs) -> None:
    if file is None:
        file = sys.stderr
    values_new: Sequence[object]
    if len(values) > 0:
        values_new = [f'{SCRIPT_IDENTITY}: {values[0]}', *values[1:]]
    else:
        values_new = values
    return print(*values_new, file=file, **kwargs)


def jinja_filter_to_pretty_json(obj, indent=2):
    return json.dumps(obj, indent=indent, ensure_ascii=False)


class _JinjaEnvironmentManager:

    def __init__(self):
        self._env = None

    @classmethod
    def create_env(cls, *, templates_path=None):
        if templates_path is None:
            templates_path = DOCS_TEMPLATES_PATH
        env = Environment(
            loader=FileSystemLoader([templates_path]),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        env.filters['escape_rst'] = escape_rst
        env.filters['to_pretty_json'] = jinja_filter_to_pretty_json
        return env

    def init(self, *, templates_path=None):
        self._env = self.create_env(templates_path=templates_path)

    def get(self):
        if self._env is None:
            self.init()
        assert self._env is not None
        return self._env


jinja_env_manager = _JinjaEnvironmentManager()


def read_schema_from_file(file):
    return json.load(file)


def open_schema_file(path):
    return open(path, 'rt', encoding='utf-8')


# XXX: ?
def read_schema_from_path(path):
    with open_schema_file(path) as file:
        return read_schema_from_file(file)


def write_rst_to_file(file, text):
    return file.write(text)


def open_rst_file_to_write(path):
    return open(path, 'wt', encoding='utf-8')


def write_rst_to_path(path, text):
    with open_rst_file_to_write(path) as file:
        return write_rst_to_file(file, text)


def doc_title_from_schema_filename(name):
    return PurePath(name).stem.replace('_', ' ').title()


def _build_schema_template_params(schema, *, title_fallback=None):
    if title_fallback is None:
        # XXX: ?
        title_fallback = TITLE_FALLBACK_NONE
    d = {}
    d['schema'] = schema
    d['title'] = (title := schema.get('title', title_fallback))
    d['schema_id'] = schema.get('$id')
    d['schema_uri'] = schema.get('$schema')
    return (d, title)


def generate_doc_for_schema(schema, *, title_fallback=None, jinja_env=None):
    if jinja_env is None:
        jinja_env = jinja_env_manager.get()
    d, title = _build_schema_template_params(schema, title_fallback=title_fallback)
    template = jinja_env.get_template('schemas/schema.rst.j2')
    doc = template.render(**d)
    return (doc, title)


def _build_schema_template_params_from_schemas_all_entry(schema_entry):
    if len(schema_entry) == 2:
        schema, info = schema_entry
    elif len(schema_entry) == 1:
        schema, = schema_entry
        info = {}
    else:
        raise ValueError(
            'schema_entry should be a tuple of 1 or 2 elemenets'
            ' (schema object and optional info dict)'
        )
    doc, title_tmp = _build_schema_template_params(
        schema,
        title_fallback=info.get('title_fallback'),
    )
    doc_name = info.get('doc_name')
    if doc_name is None:
        doc_name = title_tmp
    return (doc, doc_name)


def generate_doc_for_schemas_all(schema_entries, *, jinja_env=None):
    if jinja_env is None:
        jinja_env = jinja_env_manager.get()
    schemas_params_and_doc_names = [
        _build_schema_template_params_from_schemas_all_entry(se)
        for se in schema_entries
    ]
    schema_params_and_doc_names_by_schema_id = {
        schema_params['schema_id']: (schema_params, doc_name)
        for schema_params, doc_name in schemas_params_and_doc_names
    }
    d = {'schemas': schema_params_and_doc_names_by_schema_id}
    template = jinja_env.get_template('schemas/schemas_all.rst.j2')
    return template.render(**d)


def generate_index_doc(docs_info):
    env = jinja_env_manager.get()
    template = env.get_template('schemas/index.rst.j2')
    return template.render({'docs_info': docs_info})


def _main_impl_schema_docs_single_make_schema_entry_for_doc(schemas_path, schema_path):
    schema_relpath = schema_path.relative_to(schemas_path)
    schema = read_schema_from_path(schema_path)
    return (
        schema,
        dict(
            title_fallback=doc_title_from_schema_filename(schema_relpath.name),
            doc_name=schema_relpath.with_suffix('').as_posix(),
        ),
    )


def build_cli_args_parser(prog_name=None):
    argument_parser_kwargs_extra = {}
    if prog_name is not None:
        argument_parser_kwargs_extra['prog'] = prog_name
    parser = ArgumentParser(
        description='generate Sphinx docs for JSON schemas',
        allow_abbrev=False,
        add_help=True,
        exit_on_error=True,
        **argument_parser_kwargs_extra,
    )
    parser.add_argument(
        '-i', '--input',
        type=Path,
        help=(
            f'path to directory containing JSON schemas'
            f' (default: {SCHEMAS_REL_PATH_DEFAULT})'
        ),
        metavar='PATH',
        dest='input_path',
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help=(
            'path to output directory for reStructuredText files (default: {0})'
            .format(
                str(
                    DOCS_SOURCE_PATH.relative_to(PROJECT_PATH)
                    / OUTPUT_SOURCE_REL_PATH_DEFAULT
                ),
            )
        ),
        metavar='PATH',
        dest='output_path',
    )
    parser.add_argument(
        '--index',
        type=PurePosixPath,
        help=(
            f'POSIX relative path to output index file (relative to output_path)'
            f' (default: {INDEX_DOC_NAME_DEFAULT})'
        ),
        metavar='NAME',
        dest='index_doc_name',
    )
    parser.add_argument(
        '--purge',
        action='store_true',
        help='purge the output_path directory before generating',
        dest='do_purge',
    )
    parser.add_argument(
        '--layout',
        choices=list(map(str, LayoutMode)),
        default=str(LAYOUT_MODE_DEFAULT),
        help='layout mode',
        dest='layout_mode',
    )
    parser.add_argument(
        '--templates',
        type=Path,
        help=(
            'path to templates directory (default: {0})'
            .format(DOCS_TEMPLATES_PATH.relative_to(PROJECT_PATH))
        ),
        metavar='PATH',
        dest='templates_path',
    )
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet')
    return parser


def parse_cli_args(parser, argv_trunc):
    args = parser.parse_args(argv_trunc)
    args.layout_mode = LayoutMode(args.layout_mode)
    return args


def main(argv):  # noqa: C901
    args_parser = build_cli_args_parser(argv[0])
    # XXX: return code on error!?
    args = parse_cli_args(args_parser, argv[1:])   # may exit
    quiet = args.quiet
    output_path = (
        args.output_path
        if args.output_path is not None
        else (DOCS_SOURCE_PATH / OUTPUT_SOURCE_REL_PATH_DEFAULT)
    )
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as err:
        _print_err(
            f'error: failed to create the output directory'
            f' {str(args.output_path)!r}: {err}'
        )
        return 2
    if args.do_purge:
        try:
            purge_directory(output_path)
        except Exception as err:
            _print_err(
                f'error: failed to purge the output directory'
                f' {str(args.output_path)!r}: {err}'
            )
            return 2
    schemas_path = (
        args.input_path
        if args.input_path is not None
        else (PROJECT_PATH / SCHEMAS_REL_PATH_DEFAULT)
    )
    layout_mode = args.layout_mode
    index_doc_name = (
        args.index_doc_name
        if args.index_doc_name is not None
        else INDEX_DOC_NAME_DEFAULT
    )
    index_path = (output_path / PurePath(index_doc_name).with_suffix('.rst'))
    jinja_env_manager.init(templates_path=args.templates_path)
    if not schemas_path.is_dir():
        _print_err(
            'error: schemas directory not found: {0!r}'
            .format(str(schemas_path))
        )
        return 2
    schema_file_paths = sorted(schemas_path.rglob('*.json'))
    if (not quiet) and (len(schema_file_paths) == 0):
        _print_err(f'warning: no schema files found in {str(schemas_path)!r}')
    error_occured = False
    match layout_mode:
        case LayoutMode.SINGLE:
            schema_entries_for_doc = []
            for schema_path in schema_file_paths:
                schema_relpath = schema_path.relative_to(schemas_path)
                try:
                    schema_entry_for_doc = (
                        _main_impl_schema_docs_single_make_schema_entry_for_doc(
                            schemas_path, schema_path,
                        )
                    )
                except Exception as err:
                    _print_err(
                        'error: failed to process {0!r}: {1}'
                        .format(str(schema_path.relative_to(schemas_path)), err)
                    )
                else:
                    schema_entries_for_doc.append(schema_entry_for_doc)
            try:
                doc = generate_doc_for_schemas_all(schema_entries_for_doc)
                doc_path = (
                    output_path / PurePath(index_doc_name).with_suffix('.rst')
                )
                doc_path.parent.mkdir(parents=True, exist_ok=True)
                write_rst_to_path(doc_path, doc)
            except Exception as err:
                docs_num = 0
                _print_err(
                    'error: failed to make index doc {0!r} at {1!r}: {2!s}'
                    .format(str(index_doc_name), str(index_path), err)
                )
            else:
                docs_num = len(schema_entries_for_doc)
            if not quiet:
                _print_err(
                    f'index {str(index_doc_name)} created at {str(index_path)!r}'
                )
        case LayoutMode.MULTI:
            docs_info = []
            for schema_path in schema_file_paths:
                schema_relpath = schema_path.relative_to(schemas_path)
                doc_path = output_path / schema_relpath.with_suffix('.rst')
                try:
                    schema = read_schema_from_path(schema_path)
                    doc, doc_title = generate_doc_for_schema(
                        schema,
                        title_fallback=doc_title_from_schema_filename(
                            schema_relpath.name
                        ),
                    )
                    doc_path.parent.mkdir(parents=True, exist_ok=True)
                    write_rst_to_path(doc_path, doc)
                except Exception as err:
                    _print_err(
                        f'error:'
                        f' failed to process {str(schema_relpath)!r}: {err}'
                    )
                else:
                    doc_name = schema_relpath.with_suffix('').as_posix()
                    docs_info.append((doc_name, doc_title))
            docs_num = len(docs_info)
            if not quiet:
                _print_err(f'generated {docs_num} schema documentation files')
            try:
                index_doc = generate_index_doc(docs_info)
                index_path.parent.mkdir(parents=True, exist_ok=True)
                write_rst_to_path(index_path, index_doc)
            except Exception as err:
                error_occured = True
                _print_err(
                    'error: failed to make index doc {0!r} at {1!r}: {2!s}'
                    .format(str(index_doc_name), str(index_path), err),
                )
            else:
                _print_err(
                    f'index {str(index_doc_name)} created at {str(index_path)!r}'
                )
        case _:
            return -1
    if error_occured:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(int(main(sys.argv)))
