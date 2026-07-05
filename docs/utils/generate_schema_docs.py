# TODO: use something like "fractured JSON" for examples (pretty but fairly compact)

from argparse import ArgumentParser
from collections.abc import Iterable, Sequence
from enum import StrEnum
import json
from pathlib import PurePosixPath, PurePath, Path
import sys
from typing import cast
import warnings
from warnings import catch_warnings, warn

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


def main_impl_resolve_and_make_output_path(output_path=None):
    if output_path is None:
        output_path = DOCS_SOURCE_PATH / OUTPUT_SOURCE_REL_PATH_DEFAULT
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def main_impl_purge(output_path=None):
    output_path = main_impl_resolve_and_make_output_path(output_path)
    purge_directory(output_path)


def main_impl_resolve_schemas_path(schemas_path=None):
    if schemas_path is None:
        schemas_path = PROJECT_PATH / SCHEMAS_REL_PATH_DEFAULT
    return schemas_path


class SchemasDirectoryNotFoundError(FileNotFoundError):
    pass


class NoSchemaFilesFoundWarning(UserWarning):
    pass


def main_impl_get_schema_file_paths(schemas_path=None):
    schemas_path = main_impl_resolve_schemas_path(schemas_path)
    if not schemas_path.is_dir():
        raise SchemasDirectoryNotFoundError(str(schemas_path))
    schema_file_paths = sorted(schemas_path.rglob('*.json'))
    if len(schema_file_paths) == 0:
        warn(
            f'no schema files found in {str(schemas_path)!r}',
            NoSchemaFilesFoundWarning,
        )
    return schema_file_paths


class SchemaProcessingError(Exception):

    @classmethod
    def _make_message(cls, schema_relpath):
        return f'Could not process the schema {str(schema_relpath)!r}'

    def __init__(self, schema_relpath):
        super().__init__(self._make_message(schema_relpath))
        self.schema_relpath = schema_relpath


def main_impl_schema_docs_multi(
    schemas_path=None, output_path=None, *, jinja_env=None,
):
    schemas_path = main_impl_resolve_schemas_path(schemas_path)
    schema_file_paths = main_impl_get_schema_file_paths(schemas_path)
    output_path = main_impl_resolve_and_make_output_path(output_path)
    docs_info = []
    doc_excs = []
    for schema_path in schema_file_paths:
        schema_relpath = schema_path.relative_to(schemas_path)
        doc_path = output_path / schema_relpath.with_suffix('.rst')
        try:
            schema = read_schema_from_path(schema_path)
            doc, doc_title = generate_doc_for_schema(
                schema,
                title_fallback=doc_title_from_schema_filename(schema_relpath.name),
                jinja_env=jinja_env,
            )
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            write_rst_to_path(doc_path, doc)
        except Exception as err:
            err_2 = SchemaProcessingError(schema_relpath)
            err_2.__cause__ = err
            doc_excs.append(err_2)
        else:
            doc_name = schema_relpath.with_suffix('').as_posix()
            docs_info.append((doc_name, doc_title))
    if len(doc_excs) > 0:
        err_group = ExceptionGroup('Some schemas could not be processed', doc_excs)
    else:
        err_group = None
    return (docs_info, err_group)


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


class DocForSchemasAllProcessingError(Exception):
    pass


def main_impl_schema_docs_single(
    schemas_path=None, output_path=None,
    *, index_doc_name=INDEX_DOC_NAME_DEFAULT, jinja_env=None,
):
    schemas_path = main_impl_resolve_schemas_path(schemas_path)
    schema_file_paths = main_impl_get_schema_file_paths(schemas_path)
    output_path = main_impl_resolve_and_make_output_path(output_path)
    schema_entries_for_doc = []
    schema_entries_for_doc_excs = []
    for schema_path in schema_file_paths:
        schema_relpath = schema_path.relative_to(schemas_path)
        try:
            schema_entry_for_doc = (
                _main_impl_schema_docs_single_make_schema_entry_for_doc(
                    schemas_path, schema_path,
                )
            )
        except Exception as err:
            err_2 = SchemaProcessingError(schema_relpath)
            err_2.__cause__ = err
            schema_entries_for_doc_excs.append(err_2)
        else:
            schema_entries_for_doc.append(schema_entry_for_doc)
    try:
        doc = generate_doc_for_schemas_all(
            schema_entries_for_doc, jinja_env=jinja_env,
        )
        doc_path = output_path / PurePath(index_doc_name).with_suffix('.rst')
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path = output_path / PurePath(index_doc_name).with_suffix('.rst')
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        write_rst_to_path(doc_path, doc)
    except Exception as err:
        raise DocForSchemasAllProcessingError(str(err)) from err
    if len(schema_entries_for_doc_excs) > 0:
        err_group = ExceptionGroup(
            'Some schemas could not be processed', schema_entries_for_doc_excs
        )
    else:
        err_group = None
    return (len(schema_entries_for_doc), err_group)


def main_impl_resolve_index_path(
    output_path=None, *, index_doc_name=INDEX_DOC_NAME_DEFAULT,
):
    output_path = main_impl_resolve_and_make_output_path(output_path)
    return (output_path / PurePath(index_doc_name).with_suffix('.rst'))


def main_impl_index_doc(
    docs_info, output_path=None, *, index_doc_name=INDEX_DOC_NAME_DEFAULT,
):
    index_path = main_impl_resolve_index_path(
        output_path, index_doc_name=index_doc_name,
    )
    index_doc = generate_index_doc(docs_info)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    write_rst_to_path(index_path, index_doc)
    return index_path


def _validate_cli_examples_num_max(s):
    val = int(s)
    if val < 0:
        raise ValueError('examples-num-max must be non-negative')
    return val


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
    if args.do_purge:
        try:
            main_impl_purge(args.output_path)
        except Exception as err:
            _print_err(
                f'error: failed to purge the output directory'
                f' {str(args.output_path)!r}: {err}'
            )
            return 2
    layout_mode = args.layout_mode
    index_doc_name = (
        args.index_doc_name
        if args.index_doc_name is not None
        else INDEX_DOC_NAME_DEFAULT
    )
    jinja_env_manager.init(templates_path=args.templates_path)
    error_occured = False
    with catch_warnings(record=True) as warns:
        warnings.simplefilter('always', NoSchemaFilesFoundWarning)
        try:
            match layout_mode:
                case LayoutMode.SINGLE:
                    try:
                        docs_num, docs_err_group = main_impl_schema_docs_single(
                            args.input_path, args.output_path,
                            index_doc_name=index_doc_name,
                        )
                    except DocForSchemasAllProcessingError as err:
                        docs_num = 0
                        docs_err_group = None
                        _print_err(
                            'error: failed to make index doc {0!r} at {1!r}: {2!s}'
                            .format(
                                str(index_doc_name),
                                str(main_impl_resolve_index_path(
                                    args.output_path,
                                    index_doc_name=index_doc_name,
                                )),
                                err,
                            )
                        )
                    docs_info = None
                case LayoutMode.MULTI:
                    docs_info, docs_err_group = main_impl_schema_docs_multi(
                        args.input_path, args.output_path,
                    )
                    docs_num = len(docs_info)
                case _:
                    return -1
        except SchemasDirectoryNotFoundError:
            _print_err(
                'error: schemas directory not found: {0!r}'
                .format(str(main_impl_resolve_schemas_path(args.input_path)))
            )
            return 2
    if not quiet:
        for warning in warns:
            _print_err(f'warning: {warning.message}', file=sys.stderr)
    if docs_err_group is not None:
        error_occured = True
        err_match, err_rest = docs_err_group.split(SchemaProcessingError)
        if err_match is not None:
            for err in cast(    # type: ignore[misc]
                Iterable[SchemaProcessingError],
                err_match.exceptions
            ):
                _print_err(
                    f'error: failed to process {str(err.schema_relpath)!r}:'    # type: ignore[misc] # noqa: E501
                    f' {err.__cause__}'  # type: ignore[misc]
                )
        if err_rest is not None:
            raise err_rest
    match layout_mode:
        case LayoutMode.SINGLE:
            if not quiet:
                index_path = main_impl_resolve_index_path(
                    docs_info, index_doc_name=index_doc_name,
                )
                _print_err(
                    f'index {str(index_doc_name)} created at {str(index_path)!r}'
                )
        case LayoutMode.MULTI:
            if not quiet:
                _print_err(f'generated {docs_num} schema documentation files')
            try:
                index_path = main_impl_index_doc(
                    docs_info, args.output_path, index_doc_name=index_doc_name,
                )
            except Exception as err:
                error_occured = True
                _print_err(
                    'error: failed to make index doc {0!r} at {1!r}: {2!s}'
                    .format(
                        str(index_doc_name),
                        str(main_impl_resolve_index_path(
                            args.output_path, index_doc_name=index_doc_name,
                        )),
                        err,
                    ),
                )
            else:
                if not quiet:
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
