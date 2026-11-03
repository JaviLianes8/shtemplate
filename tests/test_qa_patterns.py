"""Handwritten contracts for range endpoints and nested pattern quoting."""

from __future__ import annotations

import pytest

from shtemplate import expand


@pytest.mark.parametrize("op", ["#", "##", "%", "%%"])
@pytest.mark.parametrize("pattern", ["[[.a.]-[.c.]]", "[[.a.]-c]", "[a-[.c.]]"])
def test_collating_symbols_are_range_endpoints(op: str, pattern: str) -> None:
    for value in "abc":
        assert expand("${V" + op + pattern + "}", {"V": value}) == ""
    for value in "-dz":
        assert expand("${V" + op + pattern + "}", {"V": value}) == value


@pytest.mark.parametrize("operator", ["=", ":="])
@pytest.mark.parametrize("word", ['"*"', "'*'", r"\*"])
def test_assignment_substitutes_the_value_after_quote_removal(operator: str, word: str) -> None:
    assignment = "${X" + operator + word + "}"
    sink: dict[str, str] = {}
    assert expand("${V##" + assignment + "}|${V##$X}", {"V": "abc"}, assigned=sink) == "|"
    assert sink == {"X": "*"}
    assert expand('${V##"' + assignment + '"}', {"V": "abc"}) == "abc"


@pytest.mark.parametrize("op", ["#", "##", "%", "%%"])
@pytest.mark.parametrize("pattern", [r'"a\}b"', r'${X:-"a\}b"}'])
def test_double_quoted_patterns_preserve_backslash_before_brace(op: str, pattern: str) -> None:
    template = "${V" + op + pattern + "}"
    assert expand(template, {"V": "a}b"}) == "a}b"
    assert expand(template, {"V": r"a\}b"}) == ""
