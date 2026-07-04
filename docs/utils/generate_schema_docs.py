from argparse import ArgumentParser
from collections.abc import Iterable
import json
from pathlib import PurePosixPath, PurePath, Path
import sys
from typing import cast
import warnings
from warnings import catch_warnings, warn

from docs.utils.common import purge_directory

from .common._meta import PROJECT_PATH, DOCS_SOURCE_PATH
from .common.rst import escape_rst


SCRIPT_IDENTITY = 'generate_schema'


SCHEMAS_REL_PATH_DEFAULT = PurePath('jsonschema_extras') / 'schemas'

OUTPUT_SOURCE_REL_PATH_DEFAULT = PurePath('schemas')

INDEX_DOC_NAME_DEFAULT = PurePosixPath('index')


TITLE_FALLBACK_NONE = '(unknown)'

INDENT = '   '  # XXX: ?


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


def generate_doc_for_schema(schema, *, title_fallback=None):
    if title_fallback is None:
        # XXX: ?
        title_fallback = TITLE_FALLBACK_NONE
    title = schema.get('title', title_fallback)
    lines: list[str] = []
    lines.extend((escape_rst(title), ('=' * len(title)), ''))
    if schema.get('deprecated', False):
        lines.extend(['.. warning::', (INDENT + 'This schema is deprecated.'), ''])
    metadata_items = []
    if (id_ := schema.get('$id')) is not None:
        metadata_items.append(f"**ID:** ``{id_}``")  # XXX: !?
    #if (schema_uri := schema.get('$schema')) is not None:
    #    metadata_items.append(f"**Spec:** ``{schema_uri}``")   # XXX: !?
    if len(metadata_items) > 0:
        lines.extend([*metadata_items, ''])
    if (description := schema.get('description')) is not None:
        lines.extend((escape_rst(description), ''))
    examples = schema.get('examples', [])
    if len(examples := schema.get('examples', ())) > 0:
        examples_title = 'Examples'
        lines.extend((examples_title, ('-' * len(examples_title)), ''))
        for example in examples:
            # XXX: ?
            example_json = json.dumps(example, indent=2, ensure_ascii=False)
            example_json_lines = example_json.split('\n')
            lines.extend([
                '.. code-block:: json',
                '',
                *(
                    ((INDENT + line) if (len(line.strip()) > 0) else '')
                    for line in example_json_lines
                ),
                '',
            ])
    if (len(lines) > 0) and (len(lines[-1].strip()) != 0):
        lines.append('')
    return ('\n'.join(lines), title)


def _make_title_for_doc_in_toc(name, title):
    # NOTE: great, reStructuredText does not support inline formatting in TOC entries
    return (
        #f'{name} \u2014 {escape_rst(title)}'
        name
    )


def generate_index_doc(docs_info):
    lines = []
    title = 'Bundled schemas'
    lines.extend([
        title,
        ('=' * len(title)),
        '',
        '.. toctree::',
        (INDENT + ':maxdepth: 1'),
        '',
        *(
            (
                INDENT
                + f'{_make_title_for_doc_in_toc(doc_name, doc_title)} <{doc_name}>'
            )
            for doc_name, doc_title in docs_info
        ),  # XXX: ?
        '',
    ])
    if (len(lines) > 0) and (len(lines[-1].strip()) != 0):
        lines.append('')
    return '\n'.join(lines)


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


class SchemaProcessingError(Exception):

    @classmethod
    def _make_message(cls, schema_relpath):
        return f'Could not process the schema {str(schema_relpath)!r}'

    def __init__(self, schema_relpath):
        super().__init__(self._make_message(schema_relpath))
        self.schema_relpath = schema_relpath


def main_impl_schema_docs(schemas_path=None, output_path=None):
    schemas_path = main_impl_resolve_schemas_path(schemas_path)
    if not schemas_path.is_dir():
        raise SchemasDirectoryNotFoundError(str(schemas_path))
    schema_file_paths = sorted(schemas_path.rglob('*.json'))
    if len(schema_file_paths) == 0:
        warn(
            f'no schema files found in {str(schemas_path)!r}',
            NoSchemaFilesFoundWarning,
        )
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


def main_impl_resolve_index_path(
    output_path=None, *, index_doc_name=INDEX_DOC_NAME_DEFAULT,
):
    output_path = main_impl_resolve_and_make_output_path(output_path)
    return (output_path / PurePath(index_doc_name))


def main_impl_index_doc(
    docs_info, output_path=None, *, index_doc_name=INDEX_DOC_NAME_DEFAULT,
):
    output_path = main_impl_resolve_and_make_output_path(output_path)
    index_path = output_path / PurePath(index_doc_name).with_suffix('.rst')
    index_doc = generate_index_doc(docs_info)
    write_rst_to_path(index_path, index_doc)
    return index_path


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
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet')
    return parser


def parse_cli_args(parser, argv_trunc):
    return parser.parse_args(argv_trunc)


def main(argv):  # noqa: C901
    args_parser = build_cli_args_parser(argv[0])
    # XXX: return code on error!?
    args = parse_cli_args(args_parser, argv[1:])   # may exit
    quiet = args.quiet
    if args.do_purge:
        try:
            main_impl_purge(args.output_path)
        except Exception as err:
            print(
                (
                    f'{SCRIPT_IDENTITY}:'
                    f' error: failed to purge the output directory: {err}'
                ),
                file=sys.stderr,
            )
            return 2
    error_occured = False
    with catch_warnings(record=True) as warns:
        warnings.simplefilter('always', NoSchemaFilesFoundWarning)
        try:
            docs_info, docs_err_group = main_impl_schema_docs(
                args.input_path, args.output_path,
            )
        except SchemasDirectoryNotFoundError:
            print(
                (
                    '{0}: error: schemas directory not found: {1!r}'
                    .format(
                        SCRIPT_IDENTITY,
                        str(main_impl_resolve_schemas_path(args.input_path)),
                    )
                ),
                file=sys.stderr,
            )
            return 2
    if not quiet:
        for warning in warns:
            print(f'{SCRIPT_IDENTITY}: warning: {warning.message}', file=sys.stderr)
    if docs_err_group is not None:
        error_occured = True
        err_match, err_rest = docs_err_group.split(SchemaProcessingError)
        if err_match is not None:
            for err in cast(    # type: ignore[misc]
                Iterable[SchemaProcessingError],
                err_match.exceptions
            ):
                print(
                    (
                        f'{SCRIPT_IDENTITY}: error:'
                        f' failed to process {str(err.schema_relpath)!r}:'  # type: ignore[misc] # noqa: E501
                        f' {err.__cause__}'  # type: ignore[misc]
                    ),
                    file=sys.stderr,
                )
        if err_rest is not None:
            raise err_rest
    if not quiet:
        print(
            (
                f'{SCRIPT_IDENTITY}:'
                f' generated {len(docs_info)} schema documentation files'
            ),
            file=sys.stderr,
        )
    index_doc_name = (
        args.index_doc_name
        if args.index_doc_name is not None
        else INDEX_DOC_NAME_DEFAULT
    )
    try:
        index_path = main_impl_index_doc(
            docs_info, args.output_path, index_doc_name=index_doc_name,
        )
    except Exception as err:
        error_occured = True
        print(
            (
                '{0}: error: failed to make index doc {1!r} at {2!r}: {3!s}'
                .format(
                    SCRIPT_IDENTITY,
                    str(index_doc_name),
                    str(main_impl_resolve_index_path(
                        args.output_path, index_doc_name=index_doc_name,
                    )),
                    err,
                ),
            ),
            file=sys.stderr,
        )
    else:
        if not quiet:
            print(
                (
                    f'{SCRIPT_IDENTITY}: index {str(index_doc_name)}'
                    f' created at {str(index_path)!r}'
                ),
                file=sys.stderr,
            )
    if error_occured:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(int(main(sys.argv)))
