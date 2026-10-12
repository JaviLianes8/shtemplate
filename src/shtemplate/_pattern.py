"""Shell pattern matching notation (POSIX.1-2024 2.14) for prefix and suffix removal.

A pattern is held as a string where a backslash makes the next character
literal. ``?`` matches one character, ``*`` any run of characters and ``[...]``
a bracket expression. Matching simulates the pattern as a small automaton, so
every prefix of a value is tested in one pass: ``O(len(value) * len(pattern))``
time with no backtracking blowups, whatever the pattern.
"""

from __future__ import annotations

import string
from collections.abc import Callable
from functools import lru_cache

from ._errors import UnsafeTemplateError

Matcher = Callable[[str], bool]
_STAR: Matcher = bool  # sentinel identity; never called

_CLASSES: dict[str, Matcher] = {
    "alnum": str.isalnum,
    "alpha": str.isalpha,
    "blank": lambda c: c in " \t",
    "cntrl": lambda c: ord(c) < 32 or ord(c) == 127,
    "digit": lambda c: c in string.digits,
    "graph": lambda c: c.isprintable() and not c.isspace(),
    "lower": str.islower,
    "print": str.isprintable,
    "punct": lambda c: c in string.punctuation,
    "space": str.isspace,
    "upper": str.isupper,
    "xdigit": lambda c: c in string.hexdigits,
}


def _never(_: str) -> bool:
    return False


def _bracket(pattern: str, start: int) -> tuple[Matcher, int] | None:
    """Parse a bracket expression at ``pattern[start] == "["``; None if invalid."""
    j = start + 1
    negate = j < len(pattern) and pattern[j] in "!^"
    j += 1 if negate else 0
    chars: set[str] = set()
    ranges: list[tuple[str, str]] = []
    tests: list[Matcher] = []
    first = True
    while j < len(pattern):
        char = pattern[j]
        if char == "]" and not first:
            return _member(negate, frozenset(chars), tuple(ranges), tuple(tests)), j + 1
        first = False
        if char == "[" and pattern[j + 1 : j + 2] in (":", "=", "."):
            kind = pattern[j + 1]
            end = pattern.find(kind + "]", j + 2)
            if end != -1:
                name = pattern[j + 2 : end]
                if kind == ":":
                    tests.append(_CLASSES.get(name, _never))
                elif len(name) == 1:
                    chars.add(name)
                j = end + 2
                continue
        low, j = _bracket_char(pattern, j)
        if pattern[j : j + 1] == "-" and j + 1 < len(pattern) and pattern[j + 1] != "]":
            high, j = _bracket_char(pattern, j + 1)
            ranges.append((low, high))
        else:
            chars.add(low)
    return None


def _bracket_char(pattern: str, j: int) -> tuple[str, int]:
    if pattern[j] == "\\" and j + 1 < len(pattern):
        return pattern[j + 1], j + 2
    return pattern[j], j + 1


def _member(
    negate: bool,
    chars: frozenset[str],
    ranges: tuple[tuple[str, str], ...],
    tests: tuple[Matcher, ...],
) -> Matcher:
    def matches(char: str) -> bool:
        found = (
            char in chars
            or any(low <= char <= high for low, high in ranges)
            or any(test(char) for test in tests)
        )
        return found != negate

    return matches


def _literal(expected: str) -> Matcher:
    return expected.__eq__


def _any(_: str) -> bool:
    return True


def compile_pattern(pattern: str) -> tuple[Matcher, ...]:
    """Turn ``pattern`` into a tuple of single-character matchers and ``_STAR`` marks."""
    if len(pattern) <= 1024:
        return _compile_cached(pattern)
    return _compile(pattern)


def _compile(pattern: str) -> tuple[Matcher, ...]:
    items: list[Matcher] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "\\" and i + 1 < len(pattern):
            items.append(_literal(pattern[i + 1]))
            i += 2
            continue
        if char == "*":
            if not items or items[-1] is not _STAR:
                items.append(_STAR)
        elif char == "?":
            items.append(_any)
        elif char == "[" and (parsed := _bracket(pattern, i)) is not None:
            items.append(parsed[0])
            i = parsed[1]
            continue
        else:
            items.append(_literal(char))
        i += 1
    return tuple(items)


_compile_cached = lru_cache(maxsize=512)(_compile)


def _closure(states: set[int], items: tuple[Matcher, ...]) -> set[int]:
    for state in sorted(states):
        index = state
        while index < len(items) and items[index] is _STAR:
            index += 1
            states.add(index)
    return states


def match_lengths(items: tuple[Matcher, ...], text: str) -> list[int]:
    """Return every ``n`` (ascending) such that ``text[:n]`` matches the whole pattern."""
    end = len(items)
    states = _closure({0}, items)
    found = [0] if end in states else []
    for count, char in enumerate(text, start=1):
        step: set[int] = set()
        for state in states:
            if state == end:
                continue
            item = items[state]
            if item is _STAR:
                step.add(state)
            elif item(char):
                step.add(state + 1)
        if not step:
            break
        states = _closure(step, items)
        if end in states:
            found.append(count)
    return found


def remove(value: str, pattern: str, op: str, work_limit: int | None = None) -> str:
    """Apply ``#``, ``##``, ``%`` or ``%%`` with ``pattern`` to ``value``.

    With ``work_limit``, raise :class:`UnsafeTemplateError` instead of matching
    when ``len(value) * len(pattern)`` (the worst-case step count) exceeds it.
    """
    items = compile_pattern(pattern)
    if work_limit is not None and len(value) * max(len(items), 1) > work_limit:
        raise UnsafeTemplateError(
            f"pattern matching would take more than {work_limit} steps "
            f"({len(value)} characters against {len(items)} pattern items)"
        )
    if op.startswith("#"):
        lengths = match_lengths(items, value)
        if not lengths:
            return value
        return value[(lengths[0] if op == "#" else lengths[-1]) :]
    lengths = match_lengths(items[::-1], value[::-1])
    if not lengths:
        return value
    cut = lengths[0] if op == "%" else lengths[-1]
    return value[: len(value) - cut]
