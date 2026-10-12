"""The complete public promise of shtemplate, one assertion per documented claim."""

from __future__ import annotations

import doctest
import importlib
import importlib.resources
import os
import re
from pathlib import Path

import pytest

import shtemplate
from shtemplate import (
    ExpansionError,
    ParameterError,
    TemplateSyntaxError,
    UnsafeTemplateError,
    UnsetVariableError,
    escape,
    expand,
    list_vars,
)

ROOT = Path(__file__).parent.parent
PYPROJECT = (ROOT / "pyproject.toml").read_text("utf-8")
PUBLIC_API: list[str] = [
    "ExpansionError",
    "ParameterError",
    "TemplateSyntaxError",
    "UnsafeTemplateError",
    "UnsetVariableError",
    "escape",
    "expand",
    "list_vars",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(shtemplate.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in shtemplate.__all__:
        assert hasattr(shtemplate, name)


def test_version_is_a_three_part_string_matching_pyproject() -> None:
    parts = shtemplate.__version__.split(".")
    assert len(parts) == 3 and all(part.isdigit() for part in parts)
    assert f'\nversion = "{shtemplate.__version__}"\n' in PYPROJECT


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("shtemplate").joinpath("py.typed").is_file()


def test_zero_runtime_dependencies_and_a_console_script() -> None:
    assert "\ndependencies = []\n" in PYPROJECT
    assert '[project.scripts]\nshtemplate = "shtemplate._cli:main"\n' in PYPROJECT


def test_error_hierarchy() -> None:
    for error in (TemplateSyntaxError, UnsetVariableError, ParameterError, UnsafeTemplateError):
        assert issubclass(error, ExpansionError)
    assert issubclass(ExpansionError, ValueError)


# Every row of the README "Supported forms" table, for set, empty and unset.
FORMS = [
    ("${V}", "val", "", ""),
    ("$V", "val", "", ""),
    ("${V:-w}", "val", "w", "w"),
    ("${V-w}", "val", "", "w"),
    ("${V:=w}", "val", "w", "w"),
    ("${V=w}", "val", "", "w"),
    ("${V:+w}", "w", "", ""),
    ("${V+w}", "w", "w", ""),
    ("${V:?w}", "val", ParameterError, ParameterError),
    ("${V?w}", "val", "", ParameterError),
    ("${#V}", "3", "0", "0"),
    ("${V%l}", "va", "", ""),
    ("${V%%a*}", "v", "", ""),
    ("${V#v}", "al", "", ""),
    ("${V##*a}", "l", "", ""),
    ("$$", "$", "$", "$"),
    ("\\$V", "$V", "$V", "$V"),
]


@pytest.mark.parametrize(("template", "when_set", "when_empty", "when_unset"), FORMS)
def test_documented_forms(
    template: str, when_set: object, when_empty: object, when_unset: object
) -> None:
    for env, expected in (({"V": "val"}, when_set), ({"V": ""}, when_empty), ({}, when_unset)):
        if isinstance(expected, type):
            with pytest.raises(expected):
                expand(template, env)
        else:
            assert expand(template, env) == expected


README_FORMS = [
    "${NAME}",
    "$NAME",
    "${NAME:-word}",
    "${NAME-word}",
    "${NAME:=word}",
    "${NAME=word}",
    "${NAME:+word}",
    "${NAME+word}",
    "${NAME:?word}",
    "${NAME?word}",
    "${#NAME}",
    "${NAME%word}",
    "${NAME%%word}",
    "${NAME#word}",
    "${NAME##word}",
    "$$",
    "\\$NAME",
]


def test_readme_table_lists_exactly_the_tested_forms() -> None:
    readme = (ROOT / "README.md").read_text("utf-8")
    table = re.findall(r"^\| `([^`]+)`", readme, flags=re.MULTILINE)
    assert table == README_FORMS
    assert len(FORMS) == len(README_FORMS)


def test_env_is_never_mutated_and_environ_is_never_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHT_CONTRACT", "from-environ")
    env = {"E": ""}
    assert expand("${SHT_CONTRACT:-none} ${E:=x} ${N=y}", env) == "none x y"
    assert env == {"E": ""}
    assert expand("$SHT_CONTRACT", os.environ) == "from-environ"


def test_list_vars_and_escape_promises() -> None:
    assert list_vars("${A:-${B}} $A ${#C}") == ["A", "B", "C"]
    text = "any $text `with` \\ specials"
    assert expand(escape(text)) == text


def test_strict_and_safe_promises() -> None:
    with pytest.raises(UnsetVariableError):
        expand("$U", {}, strict=True)
    assert expand("${U:-ok}", {}, strict=True) == "ok"
    with pytest.raises(UnsafeTemplateError):
        expand("$(id)", {}, safe=True)
    assert expand("$(id)", {}) == "$(id)"


@pytest.mark.parametrize(
    "module", ["shtemplate", "shtemplate._core", "shtemplate._tools", "shtemplate._errors"]
)
def test_docstring_examples_run(module: str) -> None:
    result = doctest.testmod(importlib.import_module(module))
    assert result.failed == 0
