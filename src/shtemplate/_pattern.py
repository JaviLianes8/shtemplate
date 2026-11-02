"""Shell pattern matching notation (POSIX.1-2024 2.14) for prefix and suffix removal.

A pattern is held as a string where a backslash makes the next character
literal. ``?`` matches one character, ``*`` any run of characters and ``[...]``
a bracket expression. Matching simulates the pattern as a small automaton, so
every prefix of a value is tested in one pass: ``O(len(value) * len(pattern))``
time with no backtracking blowups, whatever the pattern.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache

from ._bracket import _bracket
from ._errors import UnsafeTemplateError

Matcher = Callable[[str], bool]
_STAR: Matcher = bool  # sentinel identity; never called


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
    failed: set[int] = set()
    endings: dict[str, list[int]] = {}
    for match in re.finditer(r"[:=.]\]", pattern):
        endings.setdefault(match.group()[0], []).append(match.start())
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
        elif char == "[":
            parsed = _bracket(pattern, i, failed, endings)
            if parsed is not None:
                items.append(parsed[0])
                i = parsed[1]
                continue
            items.append(_literal(char))
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
    if work_limit is not None and len(value) * max(len(pattern), 1) > work_limit:
        raise UnsafeTemplateError(
            f"pattern matching would take more than {work_limit} steps "
            f"({len(value)} characters against {len(pattern)} pattern characters)"
        )
    items = compile_pattern(pattern)
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
