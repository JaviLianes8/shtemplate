"""Command line tool: expand a template from a file or stdin."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from typing import NoReturn

from . import __version__
from ._core import expand
from ._dotenv import EnvFileError, parse_env, valid_name
from ._errors import ExpansionError
from ._tools import list_vars

_EPILOG = """\
examples:
  echo 'Hello ${USER:-world}' | shtemplate
  shtemplate config.tpl -o config.ini
  shtemplate -i --env-file prod.env --set PORT=8080 config.tpl
  shtemplate --strict --safe untrusted.tpl
  shtemplate --list-vars config.tpl

variables come from the process environment, then each --env-file in order,
then each --set; later sources win. -i starts from an empty environment.
errors go to stderr and the exit status is 1.
"""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="shtemplate",
        description="Expand POSIX shell parameter expansions ($VAR, ${VAR:-default},\n"
        "${VAR%pattern}, ...) in a template. Nothing is ever executed.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add = parser.add_argument
    add("template", nargs="?", default="-", help="template file, or - for stdin (default)")
    add("-o", "--output", metavar="FILE", help="write the result to FILE instead of stdout")
    add("-e", "--env-file", metavar="FILE", action="append", default=[], help="read NAME=VALUE")
    add("-s", "--set", metavar="NAME=VALUE", action="append", default=[], help="set one variable")
    add("-i", "--ignore-environment", action="store_true", help="do not read os.environ")
    add("--strict", action="store_true", help="fail on unset variables, like set -u")
    add("--safe", action="store_true", help="reject $(...), $((...)), backquotes; cap output")
    add("--list-vars", action="store_true", help="print referenced names, one per line, and exit")
    add("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _read(path: str) -> str:
    if path == "-":
        data, label = sys.stdin.buffer.read(), "stdin"
    else:
        with open(path, "rb") as handle:
            data, label = handle.read(), path
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnvFileError(f"{label}: not valid UTF-8 (byte {exc.start})") from None


def _environment(args: argparse.Namespace) -> dict[str, str]:
    env: dict[str, str] = {} if args.ignore_environment else dict(os.environ)
    for path in args.env_file:
        env.update(parse_env(_read(path), path))
    for item in args.set:
        name, sep, value = item.partition("=")
        if not sep or not valid_name(name):
            raise EnvFileError(f"--set expects NAME=VALUE with a valid name, got {item!r}")
        env[name] = value
    return env


def _write(text: str, output: str | None) -> None:
    # surrogateescape writes back undecodable bytes taken from os.environ or argv.
    data = text.encode("utf-8", errors="surrogateescape")
    if output is None:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    else:
        with open(output, "wb") as handle:
            handle.write(data)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool; return the exit status."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        template = _read(args.template)
        if args.list_vars:
            names = list_vars(template)
            _write("".join(name + "\n" for name in names), args.output)
            return 0
        result = expand(template, _environment(args), strict=args.strict, safe=args.safe)
        _write(result, args.output)
    except (ExpansionError, EnvFileError, OSError, UnicodeError) as exc:
        print(f"shtemplate: error: {exc}", file=sys.stderr)
        return 1
    return 0
