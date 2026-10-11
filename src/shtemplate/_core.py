"""POSIX shell-style parameter expansion over a mapping."""

from __future__ import annotations

from collections.abc import Mapping

from ._errors import ExpansionError

_NAME_START = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_NAME_REST = _NAME_START | frozenset("0123456789")
_OPERATORS = frozenset("-+?")


def expand(
    template: str,
    env: Mapping[str, str] | None = None,
    *,
    strict: bool = False,
) -> str:
    """Expand ``$VAR`` and ``${VAR...}`` forms in ``template`` from ``env``.

    Supports ``${VAR}``, ``${VAR:-default}``, ``${VAR-default}``,
    ``${VAR:?message}``, ``${VAR:+alt}`` and their colon-less variants. A literal
    dollar is written ``$$``. In strict mode a plain reference to an unset
    variable raises instead of expanding to an empty string.
    """
    source: Mapping[str, str] = env if env is not None else {}
    out: list[str] = []
    i, n = 0, len(template)
    while i < n:
        char = template[i]
        if char != "$":
            out.append(char)
            i += 1
        elif i + 1 < n and template[i + 1] == "$":
            out.append("$")
            i += 2
        elif i + 1 < n and template[i + 1] == "{":
            value, i = _expand_braced(template, i + 2, source, strict)
            out.append(value)
        else:
            name, i = _read_name(template, i + 1)
            out.append(_lookup(name, source, strict) if name else "$")
    return "".join(out)


def _read_name(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] not in _NAME_START:
        return "", start
    end = start + 1
    while end < len(text) and text[end] in _NAME_REST:
        end += 1
    return text[start:end], end


def _expand_braced(text: str, start: int, env: Mapping[str, str], strict: bool) -> tuple[str, int]:
    end = text.find("}", start)
    if end == -1:
        raise ExpansionError(f"unterminated expansion: missing '}}' in {text!r}")
    return _apply(text[start:end], env, strict), end + 1


def _apply(body: str, env: Mapping[str, str], strict: bool) -> str:
    name, rest = _split_name(body)
    if not name:
        raise ExpansionError(f"invalid variable name in '${{{body}}}'")
    if not rest:
        return _lookup(name, env, strict)
    colon = rest[0] == ":"
    cursor = 1 if colon else 0
    if cursor >= len(rest) or rest[cursor] not in _OPERATORS:
        raise ExpansionError(f"unknown operator in '${{{body}}}'")
    return _apply_operator(name, rest[cursor], rest[cursor + 1 :], colon, env)


def _apply_operator(
    name: str, operator: str, word: str, colon: bool, env: Mapping[str, str]
) -> str:
    present = name in env
    value = env[name] if present else ""
    triggered = (not present or value == "") if colon else not present
    if operator == "-":
        return word if triggered else value
    if operator == "+":
        return "" if triggered else word
    message = word or f"{name}: parameter null or not set"
    if triggered:
        raise ExpansionError(message)
    return value


def _split_name(body: str) -> tuple[str, str]:
    if not body or body[0] not in _NAME_START:
        return "", body
    end = 1
    while end < len(body) and body[end] in _NAME_REST:
        end += 1
    return body[:end], body[end:]


def _lookup(name: str, env: Mapping[str, str], strict: bool) -> str:
    if name in env:
        return env[name]
    if strict:
        raise ExpansionError(f"undefined variable: {name}")
    return ""
