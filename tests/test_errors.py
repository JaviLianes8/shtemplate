"""Typed errors, positions, strict mode and safe mode."""

from __future__ import annotations

import itertools

import pytest

from shtemplate import (
    ExpansionError,
    ParameterError,
    TemplateSyntaxError,
    UnsafeTemplateError,
    UnsetVariableError,
    expand,
)


@pytest.mark.parametrize(
    ("template", "position", "text"),
    [
        ("ab${X", 2, "unterminated"),
        ("${X:-abc", 0, "unterminated"),
        ("x ${}", 2, "invalid variable name"),
        ("${1}", 0, "invalid variable name"),
        ("${#X:-a}", 0, "invalid length"),
        ("${X@y}", 0, "unknown operator '@'"),
        ("${X:x}", 0, "unknown operator 'x'"),
        ("${X:}", 0, "unknown operator '}'"),
        ("${X#'a}", 0, "unterminated single quote"),
    ],
)
def test_syntax_errors_carry_the_position(template: str, position: int, text: str) -> None:
    with pytest.raises(TemplateSyntaxError, match=text) as caught:
        expand(template, {"X": "v"})
    assert caught.value.position == position
    assert isinstance(caught.value, ExpansionError)
    assert isinstance(caught.value, ValueError)


def test_syntax_errors_are_raised_even_in_unused_words() -> None:
    with pytest.raises(TemplateSyntaxError):
        expand("${X:-${}}", {"X": "set"})


def test_nesting_depth_is_bounded() -> None:
    deep = "${A:-" * 65 + "x" + "}" * 65
    with pytest.raises(TemplateSyntaxError, match="nested deeper"):
        expand(deep, {})
    ok = "${A:-" * 64 + "x" + "}" * 64
    assert expand(ok, {}) == "x"


def test_parameter_error_has_name_detail_and_position() -> None:
    with pytest.raises(ParameterError) as caught:
        expand("key=${TOKEN:?token is required}", {})
    error = caught.value
    assert (error.name, error.detail, error.position) == ("TOKEN", "token is required", 4)
    assert str(error) == "TOKEN: token is required"


def test_parameter_error_message_is_expanded() -> None:
    with pytest.raises(ParameterError, match="X: set X in prod"):
        expand("${X:?set X in $ENV}", {"ENV": "prod"})


def test_question_without_colon_default_text() -> None:
    with pytest.raises(ParameterError, match="X: parameter not set"):
        expand("${X?}", {})


@pytest.mark.parametrize("template", ["$U", "${U}", "${#U}", "${U%a}", "${U##*}", "${A:-$U}"])
def test_strict_rejects_unset_references(template: str) -> None:
    with pytest.raises(UnsetVariableError) as caught:
        expand(template, {"A": ""}, strict=True)
    assert caught.value.name == "U"
    position = caught.value.position
    assert position is not None and template[position] == "$"


@pytest.mark.parametrize("template", ["${U:-x}", "${U-x}", "${U:+x}", "${U+x}", "${U:=x}$U"])
def test_strict_allows_operators_that_handle_unset(template: str) -> None:
    expand(template, {}, strict=True)


def test_strict_treats_empty_as_set() -> None:
    assert expand("[$E]", {"E": ""}, strict=True) == "[]"


def test_strict_error_names_variable_and_position() -> None:
    with pytest.raises(UnsetVariableError, match=r"undefined variable: NAME \(at position 3\)"):
        expand("hi $NAME", {}, strict=True)


@pytest.mark.parametrize(
    ("template", "kind"),
    [
        ("a $(id)", "command substitution"),
        ("a `id`", "backquote"),
        ("$((1+2))", "arithmetic"),
        ("${X:-$(id)}", "command substitution"),
        ("${X:-`id`}", "backquote"),
    ],
)
def test_safe_mode_rejects_command_substitution(template: str, kind: str) -> None:
    with pytest.raises(UnsafeTemplateError, match=kind):
        expand(template, {"X": "v"}, safe=True)
    assert "$" in expand(template, {}) or "`" in expand(template, {})


def test_safe_mode_allows_escaped_backquotes_and_dollars() -> None:
    assert expand("\\`id\\` \\$(id)", {}, safe=True) == "`id` $(id)"


def test_safe_mode_caps_exponential_assignment_growth() -> None:
    names = [f"V{i}" for i in range(30)]
    template = "${V0:=xx}" + "".join(f"${{{b}:=${a}${a}}}" for a, b in itertools.pairwise(names))
    with pytest.raises(UnsafeTemplateError, match="exceeds the limit"):
        expand(template, {}, safe=True)


def test_max_output_applies_without_safe_mode() -> None:
    with pytest.raises(UnsafeTemplateError):
        expand("$A$A", {"A": "x" * 10}, max_output=15)
    assert expand("$A", {"A": "x" * 10}, max_output=10) == "x" * 10


def test_assigned_is_untouched_when_expansion_fails() -> None:
    sink: dict[str, str] = {}
    with pytest.raises(ParameterError):
        expand("${A:=1}${B:?}", {}, assigned=sink)
    assert sink == {}
