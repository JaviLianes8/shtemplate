"""Stable signatures, diagnostics and hostile-input contracts for version 1."""

from __future__ import annotations

import inspect
import time
from typing import cast

import pytest
from test_cli import run

import shtemplate
from shtemplate import ParameterError, UnsafeTemplateError, UnsetVariableError, expand


def test_public_names_have_examples() -> None:
    for name in shtemplate.__all__:
        assert ">>>" in (getattr(shtemplate, name).__doc__ or "")


def test_expand_signature_is_stable() -> None:
    parameters = inspect.signature(expand).parameters
    assert list(parameters) == ["template", "env", "strict", "safe", "assigned", "max_output"]
    for name, default in [
        ("strict", False),
        ("safe", False),
        ("assigned", None),
        ("max_output", None),
    ]:
        assert parameters[name].kind == inspect.Parameter.KEYWORD_ONLY
        assert parameters[name].default is default
    assert parameters["env"].default is None


def test_required_value_diagnostics_never_print_expanded_secrets() -> None:
    secret = "private-credential-" * 10000
    with pytest.raises(ParameterError) as caught:
        expand("prefix ${REQUIRED:?$SECRET}", {"SECRET": secret})
    error = caught.value
    assert error.detail == secret
    assert (error.name, error.position) == ("REQUIRED", 7)
    assert str(error) == "REQUIRED: required parameter is missing"
    assert secret not in repr(error)
    assert error.args == (str(error),)


def test_long_variable_names_do_not_make_large_diagnostics() -> None:
    name = "X" * 100000
    for template, error_type in [
        ("$" + name, UnsetVariableError),
        ("${" + name + ":?}", ParameterError),
    ]:
        with pytest.raises(error_type) as caught:
            expand(template, strict=True)
        assert isinstance(caught.value, (UnsetVariableError, ParameterError))
        assert caught.value.name == name
        assert len(str(caught.value)) < 100
        assert "<name omitted>" in str(caught.value)


@pytest.mark.parametrize("length", [80, 81])
def test_error_name_display_boundary(length: int) -> None:
    name = "A" * length
    label = name if length == 80 else "<name omitted>"
    assert str(ParameterError(name, "private", 0)) == f"{label}: required parameter is missing"
    assert str(UnsetVariableError(name, 0)) == f"undefined variable: {label} (at position 0)"


@pytest.mark.parametrize(
    "argv", [["--set", "1bad=private"], ["--private-value"], ["--set=private", "--unknown"]]
)
def test_cli_diagnostics_do_not_echo_arguments(
    monkeypatch: pytest.MonkeyPatch, argv: list[str]
) -> None:
    code, out, err = run(monkeypatch, argv)
    assert (code, out) == (1, "")
    assert "private" not in err
    assert len(err) < 1000


def test_cli_required_error_hides_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    code, out, err = run(monkeypatch, ["-i", "-s", "SECRET=private"], "${X:?$SECRET}")
    assert (code, out) == (1, "")
    assert "private" not in err


@pytest.mark.parametrize("limit", [True, 1.5, "100", object()])
def test_output_limit_rejects_wrong_types(limit: object) -> None:
    with pytest.raises(TypeError, match="max_output must be an integer or None"):
        expand("", max_output=cast(int, limit))


def test_output_limit_rejects_negative_numbers_even_for_empty_input() -> None:
    with pytest.raises(ValueError, match="max_output must be non-negative"):
        expand("", max_output=-1)


def test_zero_output_limit_and_exact_boundary() -> None:
    assert expand("$MISSING", max_output=0) == ""
    with pytest.raises(UnsafeTemplateError):
        expand("a", max_output=0)
    assert expand("$X$X", {"X": "abc"}, max_output=6) == "abcabc"
    with pytest.raises(UnsafeTemplateError):
        expand("$X$X", {"X": "abc"}, max_output=5)


@pytest.mark.parametrize("unit", ["[", "[:", "[=", "[.", "[a", "[[:"])
def test_unclosed_pattern_brackets_do_not_rescan_the_tail(unit: str) -> None:
    started = time.perf_counter()
    for size in (1000, 4000, 16000):
        pattern = unit * size
        assert expand("${V#$P}", {"V": "x", "P": pattern}, safe=True) == "x"
        assert expand("${V#$P}", {"V": "x", "P": pattern + "[:unknown:]"}, safe=True) == "x"
    assert time.perf_counter() - started < 5


def test_pattern_class_scanning_preserves_later_valid_classes() -> None:
    assert expand("${V#[[:digit:][:alpha:]]}", {"V": "a1"}) == "1"
    assert expand("${V#[[:digit:][:alpha:]]}", {"V": "1a"}) == "a"
    assert expand("${V#[]a]}", {"V": "]a"}) == "a"


@pytest.mark.parametrize("pattern", ["[[.a.]", "[[=a=]", "[[:a:]", "[a[:a:]"])
def test_incomplete_outer_bracket_preserves_inner_pattern(pattern: str) -> None:
    prefix = "[a" if pattern.startswith("[a") else "["
    assert expand("${V#$P}", {"V": prefix + "aX", "P": pattern}) == "X"


def test_pattern_work_budget_counts_bracket_members() -> None:
    with pytest.raises(UnsafeTemplateError, match="pattern matching would take more than"):
        expand("${V##$P}", {"V": "a" * 1000, "P": "*[" + "b-z" * 100 + "]"}, max_output=1000)
