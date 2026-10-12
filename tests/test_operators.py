"""Operators added in 0.2.0: length, pattern removal, assignment, nesting, quoting."""

from __future__ import annotations

import pytest

from shtemplate import expand

ENV = {"F": "archive.tar.gz", "P": "/usr/local/bin", "E": "", "S": "*.", "A": "abc"}


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("${F%.*}", "archive.tar"),
        ("${F%%.*}", "archive"),
        ("${F#*.}", "tar.gz"),
        ("${F##*.}", "gz"),
        ("${P%/*}", "/usr/local"),
        ("${P##*/}", "bin"),
        ("${P#/usr}", "/local/bin"),
        ("${F%.zip}", "archive.tar.gz"),
        ("${F#}", "archive.tar.gz"),
        ("${F#?}", "rchive.tar.gz"),
        ("${F%[a-z][a-z]}", "archive.tar."),
        ("${F#[!a]}", "archive.tar.gz"),
        ("${F#[[:alpha:]]*[.]}", "tar.gz"),
        ("${F##[[:alpha:]]*[.]}", "gz"),
        ("${MISSING%x}", ""),
    ],
)
def test_pattern_removal(template: str, expected: str) -> None:
    assert expand(template, ENV) == expected


def test_length_counts_characters() -> None:
    assert expand("${#F} ${#E} ${#MISSING}", ENV) == "14 0 0"
    assert expand("${#U}", {"U": "été"}) == "3"


def test_quoted_pattern_characters_match_literally() -> None:
    env = {"V": "*.txt"}
    assert expand("${V#'*'}", env) == ".txt"
    assert expand('${V#"*"}', env) == ".txt"
    assert expand("${V#\\*}", env) == ".txt"
    assert expand("${V#*}", env) == "*.txt"


def test_pattern_from_a_variable_is_active_unless_quoted() -> None:
    env = {"V": "a.b.c", "PAT": "*."}
    assert expand("${V#$PAT}", env) == "b.c"
    assert expand('${V#"$PAT"}', env) == "a.b.c"


def test_word_is_expanded_and_may_nest() -> None:
    assert expand("${U:-${V:-${W:-deep}}}", {}) == "deep"
    assert expand("${U:-$A/x}", ENV) == "abc/x"
    assert expand("${A:+[$A]}", ENV) == "[abc]"


def test_word_is_not_expanded_when_not_needed() -> None:
    assert expand("${A:-${U:?never raised}}", ENV) == "abc"
    assert expand("${U:+${U:?never raised}}", {}) == ""


def test_closing_brace_is_found_by_recursive_scan() -> None:
    assert expand("${U:-a\\}b}", {}) == "a}b"
    assert expand('${U:-"x}"y}', {}) == "x}y"
    assert expand("${U:-{a}b}", {}) == "{ab}"


def test_single_quotes_are_literal_in_defaulting_words() -> None:
    assert expand("${U:-'a b'}", {}) == "'a b'"


def test_assignment_is_visible_later_but_never_mutates_env() -> None:
    env: dict[str, str] = {"E": ""}
    assert expand("${U:=v}-$U ${E:=w}-$E", env) == "v-v w-w"
    assert env == {"E": ""}


def test_assignment_without_colon_keeps_an_empty_value() -> None:
    assert expand("${E=zz}[$E]", {"E": ""}) == "[]"
    assert expand("${A=zz}", ENV) == "abc"


def test_assigned_collects_the_assignments() -> None:
    sink: dict[str, str] = {}
    assert expand("${U:=one}${V=two}${A:=no}", ENV, assigned=sink) == "onetwoabc"
    assert sink == {"U": "one", "V": "two"}


def test_assigned_can_be_the_env_itself() -> None:
    env = {"X": ""}
    expand("${X:=filled}", env, assigned=env)
    assert env == {"X": "filled"}


def test_backslash_escapes_follow_here_document_rules() -> None:
    assert expand("\\$A \\\\ \\a \\` \\}", ENV) == "$A \\ \\a ` \\}"
    assert expand("one\\\ntwo", {}) == "onetwo"


def test_quotes_at_top_level_are_literal() -> None:
    assert expand("'$A' \"$A\"", ENV) == "'abc' \"abc\""


def test_dollar_cases_that_stay_literal() -> None:
    text = "$ $1 $@ $- $? $(cmd) `cmd` $((1+2))"
    assert expand(text, {}) == text
    assert expand("$$", {}) == "$"


def test_longest_name_is_used_without_braces() -> None:
    assert expand("$Ab ${A}b", ENV) == " abcb"


def test_os_environ_style_mapping_works() -> None:
    class Env(dict[str, str]):
        pass

    assert expand("${X:-d}", Env(X="v")) == "v"
