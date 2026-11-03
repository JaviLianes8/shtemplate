"""Handwritten boundary contracts for the stable defaults and diagnostics."""

from __future__ import annotations

import os

import pytest

from shtemplate import ExpansionError, TemplateSyntaxError, UnsafeTemplateError, escape, expand


def test_default_safe_output_cap_exact_boundary() -> None:
    value = "x" * 1_000_000
    assert expand("$X", {"X": value}, safe=True) == value
    with pytest.raises(UnsafeTemplateError):
        expand("$X", {"X": value + "x"}, safe=True)


def test_pattern_work_budget_is_exactly_ten_times_output_limit() -> None:
    assert expand("${V#$P}", {"V": "a" * 10, "P": "?" * 10}, max_output=10) == ""
    with pytest.raises(UnsafeTemplateError, match="pattern matching") as caught:
        expand("${V#$P}", {"V": "a" * 11, "P": "?" * 10}, max_output=10)
    assert caught.value.position is None


def test_error_positions_are_unknown_by_default() -> None:
    for error in (ExpansionError, TemplateSyntaxError, UnsafeTemplateError):
        assert error("message").position is None
    with pytest.raises(UnsafeTemplateError) as caught:
        expand("prefix $X", {"X": "abc"}, max_output=7)
    assert caught.value.position is None


def test_default_environment_does_not_read_process_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHT_BOUNDARY_DEFAULT", "process-value")
    assert expand("$SHT_BOUNDARY_DEFAULT") == ""
    assert expand("$SHT_BOUNDARY_DEFAULT", None) == ""
    assert expand("$SHT_BOUNDARY_DEFAULT", os.environ) == "process-value"


@pytest.mark.parametrize("template", ["$(echo $X)", "`echo $X`", "$((1+$X))"])
def test_command_like_text_still_evaluates_nested_parameters(template: str) -> None:
    assert expand(template, {"X": "changed"}) == template.replace("$X", "changed")
    sink: dict[str, str] = {}
    assert expand(template.replace("$X", "${X:=changed}"), assigned=sink) == template.replace(
        "$X", "changed"
    )
    assert sink == {"X": "changed"}


def test_escape_round_trip_includes_nul_in_python() -> None:
    text = "before\x00after"
    assert expand(escape(text)) == text
