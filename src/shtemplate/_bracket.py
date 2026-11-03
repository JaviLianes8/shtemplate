"""Parse POSIX bracket expressions without rescanning malformed tails."""

from __future__ import annotations

import string
from bisect import bisect_left
from collections.abc import Callable

Matcher = Callable[[str], bool]

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


def _bracket(
    pattern: str, start: int, failed: set[int], endings: dict[str, list[int]]
) -> tuple[Matcher, int] | None:
    """Parse a bracket expression at ``pattern[start] == "["``; None if invalid."""
    j = start + 1
    negate = j < len(pattern) and pattern[j] in "!^"
    j += 1 if negate else 0
    chars: set[str] = set()
    ranges: list[tuple[str, str]] = []
    tests: list[Matcher] = []
    visited: list[int] = []
    first = True
    while j < len(pattern):
        char = pattern[j]
        if char == "]" and not first:
            return _member(negate, frozenset(chars), tuple(ranges), tuple(tests)), j + 1
        if char != "]":
            if j in failed:
                failed.update(visited)
                return None
            visited.append(j)
        first = False
        if char == "[" and pattern[j + 1 : j + 2] in (":", "=", "."):
            kind = pattern[j + 1]
            positions = endings.get(kind, [])
            index = bisect_left(positions, j + 2)
            if index < len(positions):
                end = positions[index]
                size = end - j - 2
                if kind == "." and size == 1:
                    low, j = pattern[j + 2], end + 2
                elif kind == ":":
                    name = pattern[j + 2 : end] if size <= 6 else ""
                    tests.append(_CLASSES.get(name, _never))
                    j = end + 2
                    continue
                else:
                    if size == 1:
                        chars.add(pattern[j + 2])
                    j = end + 2
                    continue
            else:
                low, j = _bracket_char(pattern, j)
        else:
            low, j = _bracket_char(pattern, j)
        if pattern[j : j + 1] == "-" and j + 1 < len(pattern) and pattern[j + 1] != "]":
            high, j = _bracket_char(pattern, j + 1)
            ranges.append((low, high))
        else:
            chars.add(low)
    failed.update(visited)
    return None


def _bracket_char(pattern: str, j: int) -> tuple[str, int]:
    if pattern[j : j + 2] == "[." and pattern[j + 3 : j + 5] == ".]":
        return pattern[j + 2], j + 5
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
