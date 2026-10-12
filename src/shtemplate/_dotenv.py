"""Read ``.env``-style files for the command line tool.

One ``NAME=VALUE`` per line. Blank lines and lines starting with ``#`` are
skipped and an optional ``export`` prefix is ignored. Values may be bare (a
blank followed by ``#`` starts a comment; surrounding blanks are trimmed),
single-quoted (taken literally) or double-quoted (``\\n``, ``\\t``, ``\\r``,
``\\"``, ``\\\\`` and ``\\$`` are unescaped). Values are never expanded.
"""

from __future__ import annotations

import re

from ._nodes import NAME_REST, NAME_START

_COMMENT = re.compile(r"\s#")
_DQ_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "$": "$"}


class EnvFileError(ValueError):
    """A line of an env file cannot be parsed."""


def parse_env(text: str, source: str = "<env>") -> dict[str, str]:
    """Parse ``.env``-style ``text`` into a dict; ``source`` names it in errors."""
    values: dict[str, str] = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export ") or line.startswith("export\t"):
            line = line[7:].lstrip()
        name, sep, rest = line.partition("=")
        name = name.rstrip()
        if not sep or not _valid_name(name):
            raise EnvFileError(f"{source}:{number}: expected NAME=VALUE")
        try:
            values[name] = _value(rest.strip())
        except ValueError as exc:
            raise EnvFileError(f"{source}:{number}: {exc}") from None
    return values


def _valid_name(name: str) -> bool:
    return bool(name) and name[0] in NAME_START and all(c in NAME_REST for c in name)


def _value(rest: str) -> str:
    if rest.startswith("'"):
        end = rest.find("'", 1)
        if end == -1:
            raise ValueError("unterminated single quote")
        _trailing(rest[end + 1 :])
        return rest[1:end]
    if rest.startswith('"'):
        out: list[str] = []
        i = 1
        while i < len(rest):
            char = rest[i]
            if char == "\\" and i + 1 < len(rest):
                out.append(_DQ_ESCAPES.get(rest[i + 1], "\\" + rest[i + 1]))
                i += 2
                continue
            if char == '"':
                _trailing(rest[i + 1 :])
                return "".join(out)
            out.append(char)
            i += 1
        raise ValueError("unterminated double quote")
    comment = _COMMENT.search(rest)
    return (rest[: comment.start()] if comment else rest).strip()


def _trailing(tail: str) -> None:
    tail = tail.strip()
    if tail and not tail.startswith("#"):
        raise ValueError("unexpected text after the closing quote")
