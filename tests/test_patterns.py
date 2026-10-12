"""Pattern matching notation (POSIX.1-2024 2.14) used by the removal operators."""

from __future__ import annotations

import time

import pytest

from shtemplate._pattern import compile_pattern, match_lengths, remove


def lengths(pattern: str, text: str) -> list[int]:
    return match_lengths(compile_pattern(pattern), text)


@pytest.mark.parametrize(
    ("pattern", "text", "expected"),
    [
        ("", "abc", [0]),
        ("*", "ab", [0, 1, 2]),
        ("a*", "aba", [1, 2, 3]),
        ("?", "ab", [1]),
        ("a?c", "abcd", [3]),
        ("\\*", "*x", [1]),
        ("\\*", "ax", []),
        ("[abc]", "b", [1]),
        ("[!abc]", "b", []),
        ("[^abc]", "d", [1]),
        ("[a-c]x", "bx", [2]),
        ("[z-a]", "m", []),
        ("[]a]", "]", [1]),
        ("[!]a]", "b", [1]),
        ("[a-]", "-", [1]),
        ("[[:digit:]]*", "4u", [1, 2]),
        ("[[:space:][:punct:]]", ".", [1]),
        ("[[:nope:]]", "a", []),
        ("[[=a=]]", "a", [1]),
        ("[[.a.]]", "a", [1]),
        ("[\\]]", "]", [1]),
        ("[", "[", [1]),
        ("[!]", "[!]", [3]),
        ("a\\", "a\\", [2]),
    ],
)
def test_prefix_match_lengths(pattern: str, text: str, expected: list[int]) -> None:
    assert lengths(pattern, text) == expected


@pytest.mark.parametrize(
    ("name", "inside", "outside"),
    [
        ("alpha", "aéZ", "1_"),
        ("alnum", "a1", "_-"),
        ("upper", "AZ", "az"),
        ("lower", "az", "AZ"),
        ("blank", " \t", "\nx"),
        ("space", " \n\t", "x"),
        ("cntrl", "\x01\x7f", "a "),
        ("print", "a ", "\x01"),
        ("graph", "a!", " \x01"),
        ("punct", "!.~", "a "),
        ("xdigit", "09afAF", "gG"),
        ("digit", "09", "a"),
    ],
)
def test_character_classes(name: str, inside: str, outside: str) -> None:
    for char in inside:
        assert lengths(f"[[:{name}:]]", char) == [1], (name, char)
    for char in outside:
        assert lengths(f"[[:{name}:]]", char) == [], (name, char)


@pytest.mark.parametrize(
    ("op", "expected"),
    [("#", "b.c.d"), ("##", "d"), ("%", "a.b.c"), ("%%", "a")],
)
def test_remove_picks_shortest_or_longest(op: str, expected: str) -> None:
    pattern = "*." if op.startswith("#") else ".*"
    assert remove("a.b.c.d", pattern, op) == expected


def test_remove_without_match_returns_value() -> None:
    assert remove("abc", "x*", "##") == "abc"
    assert remove("abc", "*x", "%%") == "abc"


def test_matching_has_no_catastrophic_backtracking() -> None:
    value = "a" * 3000
    pattern = "*a*a*a*a*a*a*a*b"
    start = time.perf_counter()
    for op in ("#", "##", "%", "%%"):
        assert remove(value, pattern, op) == value
    assert time.perf_counter() - start < 5
