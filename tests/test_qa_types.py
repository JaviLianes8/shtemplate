"""Handwritten runtime type contracts, including scalar subclasses."""

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping, MutableMapping
from types import MappingProxyType
from typing import cast

import pytest

from shtemplate import UnsafeTemplateError, escape, expand, list_vars


class ShortText(str):
    def __len__(self) -> int:
        return 0

    def __str__(self) -> str:
        return ""


class PermissiveInt(int):
    def __lt__(self, other: object) -> bool:
        return False

    def __gt__(self, other: object) -> bool:
        return False

    def __int__(self) -> int:
        return 1_000_000


def test_string_subclasses_cannot_bypass_output_limits() -> None:
    value = ShortText("x" * 1_000_001)
    with pytest.raises(UnsafeTemplateError):
        expand("$X", {"X": value}, safe=True)
    with pytest.raises(UnsafeTemplateError):
        expand(value, safe=True)
    assert expand("${#X}", {"X": ShortText("abc")}) == "3"
    assert escape(ShortText("$X")) == r"\$X"


def test_integer_subclasses_use_the_underlying_limit() -> None:
    with pytest.raises(UnsafeTemplateError):
        expand("xx", max_output=PermissiveInt(1))
    with pytest.raises(ValueError):
        expand("", max_output=PermissiveInt(-1))


def test_unhashable_string_subclasses_work_at_both_parser_entry_points() -> None:
    class Unhashable(str):
        __hash__ = None  # type: ignore[assignment]

    assert expand(Unhashable("${X:-abc}")) == "abc"
    assert list_vars(Unhashable("$X")) == ["X"]


@pytest.mark.parametrize("value", [b"", b"abc", [], {}, 1, False, None])
def test_text_arguments_consistently_reject_non_strings(value: object) -> None:
    for function in (expand, escape, list_vars):
        with pytest.raises(TypeError, match="must be a string"):
            function(cast(str, value))


@pytest.mark.parametrize("value", [[], b"", False, 1])
def test_environment_requires_a_mapping_even_without_references(value: object) -> None:
    for template in ("", "$X"):
        with pytest.raises(TypeError, match="env must be a mapping or None"):
            expand(template, cast(Mapping[str, str], value))


@pytest.mark.parametrize("value", [[], (), False, 1])
def test_assignment_sink_requires_a_mutable_mapping(value: object) -> None:
    with pytest.raises(TypeError, match="assigned must be a mutable mapping or None"):
        expand("", assigned=cast(MutableMapping[str, str], value))


@pytest.mark.parametrize("template", ["", "${X:=value}"])
def test_read_only_assignment_sink_raises_type_error(template: str) -> None:
    sink = MappingProxyType({"kept": "original"})
    with pytest.raises(TypeError, match="assigned must be a mutable mapping or None"):
        expand(template, assigned=cast(MutableMapping[str, str], sink))
    assert dict(sink) == {"kept": "original"}


def test_assignment_sink_accepts_mutable_mapping() -> None:
    sink = UserDict({"kept": "original"})
    assert expand("", assigned=sink) == ""
    assert sink == {"kept": "original"}
    assert expand("${X:=value}", assigned=sink) == "value"
    assert sink == {"kept": "original", "X": "value"}


@pytest.mark.parametrize("value", [None, b"", 0, False, [], {}])
def test_fetched_values_must_be_strings(value: object) -> None:
    env = {"X": cast(str, value)}
    with pytest.raises(TypeError, match="environment values must be strings"):
        expand("${X:-fallback}", env)
    assert expand("${Y:-ok}", env) == "ok"


@pytest.mark.parametrize("value", [0, 1, "yes", None])
def test_mode_arguments_require_booleans(value: object) -> None:
    with pytest.raises(TypeError, match="strict must be a boolean"):
        expand("", strict=cast(bool, value))
    with pytest.raises(TypeError, match="safe must be a boolean"):
        expand("", safe=cast(bool, value))
