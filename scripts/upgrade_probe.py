"""Exercise the installed distribution before and after upgrading from PyPI."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys
from typing import cast

import shtemplate
from shtemplate import (
    ParameterError,
    UnsafeTemplateError,
    UnsetVariableError,
    escape,
    expand,
    list_vars,
)


def main() -> None:
    expected = sys.argv[1]
    assert shtemplate.__version__ == importlib.metadata.version("shtemplate") == expected
    legacy = expected == "0.2.1"
    assert sorted(shtemplate.__all__) == sorted(
        [
            "ExpansionError",
            "ParameterError",
            "TemplateSyntaxError",
            "UnsafeTemplateError",
            "UnsetVariableError",
            "escape",
            "expand",
            "list_vars",
        ]
    )
    env = {"X": "abc.tar.gz", "E": ""}
    sink: dict[str, str] = {}
    assert expand("${X%.*}|${X%%.*}|${X#*.}|${X##*.}", env) == "abc.tar|abc|tar.gz|gz"
    assert expand("${E:-d}|${E-d}|${E:+x}|${E+x}|${#X}", env) == "d|||x|10"
    assert expand("${U:=v}$U", env, assigned=sink) == "vv"
    assert sink == {"U": "v"} and "U" not in env
    assert list_vars("${A:-$B} ${#A}") == ["A", "B"]
    assert expand(escape("$x `y` \\"), safe=True) == "$x `y` \\"
    try:
        expand("${X:?$SECRET}", {"SECRET": "private"})
    except ParameterError as error:
        assert (error.name, error.detail, error.position) == ("X", "private", 0)
        assert str(error) == ("X: private" if legacy else "X: required parameter is missing")
    else:
        raise AssertionError("required value accepted")
    try:
        expand("$" + "A" * 1000, strict=True)
    except UnsetVariableError as error:
        assert len(error.name) == 1000
        assert (len(str(error)) > 1000) == legacy
    for limit in (True, 1.5):
        try:
            result = expand("a", max_output=cast(int, limit))
        except TypeError:
            assert not legacy
        else:
            assert legacy and result == "a"
    try:
        expand("", max_output=-1)
    except ValueError as error:
        assert type(error).__name__ == ("UnsafeTemplateError" if legacy else "ValueError")
    else:
        raise AssertionError("negative limit accepted")
    for args in (["-s", "1bad=private"], ["--private"]):
        result = subprocess.run(
            [sys.executable, "-m", "shtemplate", *args],
            input="",
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 1 and result.stdout == ""
        assert ("private" in result.stderr) == legacy
    assert expand("${V#$P}", {"V": "x", "P": "[" * 100}) == "x"
    try:
        result = expand("${V##$P}", {"V": "a" * 100, "P": "*[" + "b-z" * 10 + "]"}, max_output=100)
    except UnsafeTemplateError:
        assert not legacy
    else:
        assert legacy and result == "a" * 100
    print(f"upgrade probe {expected}: passed")


if __name__ == "__main__":
    main()
