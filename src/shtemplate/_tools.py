"""Helpers that work on a template without expanding it."""

from __future__ import annotations

from ._parser import Node, Param, parse

_ESCAPES = {"\\": "\\\\", "$": "\\$", "`": "\\`"}


def list_vars(template: str) -> list[str]:
    """Return every variable name ``template`` references, in order of first use.

    Names inside operator words are included even when that word would not be
    needed, so the result is the full set of names the template may read.
    Nothing is expanded and no mapping is needed.

    Raises:
        TemplateSyntaxError: The template is malformed.

    Examples:
        >>> list_vars("$HOME/${APP:-demo}/${APP_DIR:-$HOME/.app}")
        ['HOME', 'APP', 'APP_DIR']
    """
    seen: dict[str, None] = {}
    _collect(parse(template).nodes, seen)
    return list(seen)


def _collect(nodes: tuple[Node, ...], seen: dict[str, None]) -> None:
    for node in nodes:
        if isinstance(node, Param):
            seen.setdefault(node.name, None)
            _collect(node.word, seen)


def escape(text: str) -> str:
    r"""Return a template that expands to exactly ``text``.

    Backslash, dollar and backquote are escaped with a backslash, so
    ``expand(escape(text)) == text`` for every string, and a POSIX shell reading
    the result as a here-document body prints ``text`` too.

    Examples:
        >>> print(escape(r"cost: $5 \o/"))
        cost: \$5 \\o/
    """
    return "".join(_ESCAPES.get(char, char) for char in text)
