# flake8: noqa: E265

from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys


DOCS_UTILS_PATH = Path(__file__).parent
assert DOCS_UTILS_PATH.is_absolute()

DOCS_PATH = DOCS_UTILS_PATH.parents[0]


EXCLUDE_PATTERNS = [
    '**/tests/*',
]


def build_cli_args_parser(prog_name=None):
    argument_parser_kwargs_extra = {}
    if prog_name is not None:
        argument_parser_kwargs_extra['prog'] = prog_name
    parser = ArgumentParser(
        description=(
            'run sphinx-apidoc with some added EXCLUDE_PATTERN\'s'
            ' and some fixed options'
        ),
        allow_abbrev=False,
        add_help=True,
        exit_on_error=True,
        **argument_parser_kwargs_extra,
    )
    parser.add_argument('module_path', help='path to module to document')
    parser.add_argument(
        'exclude_patterns',
        nargs='*',
        help='fnmatch-style file and/or directory patterns to exclude from generation',
    )
    parser.add_argument(
        '-o', '--output-dir',
        required=True,
        help='directory to place all output',
        metavar='DEST_DIR',
        dest='output_dir',
    )
    return parser


def parse_known_cli_args(parser, argv_trunc):
    return parser.parse_known_args(argv_trunc)


def main_impl(unknown_flags, module_path, output_dir, exclude_patterns=()):
    apidoc_argv = [
        'sphinx-apidoc',
        '--separate',
        '--module-first',
        *unknown_flags,
        '-o', str(output_dir), module_path,
        *EXCLUDE_PATTERNS, *exclude_patterns,
    ]
    result = subprocess.run(apidoc_argv)
    return result.returncode


def main(argv):
    args_parser = build_cli_args_parser(argv[0])
    # XXX: return code on error!?
    args, unknown_flags = parse_known_cli_args(args_parser, argv[1:])   # may exit
    returncode = main_impl(
        unknown_flags, args.module_path, args.output_dir,
        exclude_patterns=args.exclude_patterns,
    )
    return returncode


if __name__ == '__main__':
    sys.exit(int(main(sys.argv)))
