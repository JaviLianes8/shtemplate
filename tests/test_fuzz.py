"""Seeded fuzzing: no crash, no hang and nothing ever executed."""

from __future__ import annotations

import os
import random
import subprocess
import time
from pathlib import Path

import pytest

from shtemplate import ExpansionError, escape, expand, list_vars

ALPHABET = [*("${}:-=?+#%*[]!^'\"\\`()ab_ \n."), "${", "$(", "${A", "${#", "[[:alpha:]]"]
ENV = {"A": "a*b", "B": "", "C": "[x]", "a": "\\", "b": "${A}"}


def random_template(rng: random.Random) -> str:
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 40)))


@pytest.fixture
def no_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("a process was started")

    monkeypatch.setattr(subprocess, "Popen", refuse)
    monkeypatch.setattr(os, "system", refuse)
    monkeypatch.setattr(os, "popen", refuse)
    for name in ("execv", "execve", "execvp", "spawnv", "spawnve", "startfile"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, refuse)


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.usefixtures("no_execution")
def test_random_templates_only_raise_expansion_errors(seed: int) -> None:
    rng = random.Random(seed)
    start = time.perf_counter()
    for _ in range(2500):
        template = random_template(rng)
        strict, safe = rng.random() < 0.3, rng.random() < 0.3
        try:
            result = expand(template, ENV, strict=strict, safe=safe)
        except ExpansionError as exc:
            assert exc.position is None or 0 <= exc.position <= len(template)
            continue
        assert isinstance(result, str)
        assert isinstance(list_vars(template), list)
    assert time.perf_counter() - start < 30


@pytest.mark.usefixtures("no_execution")
def test_command_substitution_is_never_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "pwned"
    templates = [
        "$(touch pwned)",
        "`touch pwned`",
        "${X:-$(touch pwned)}",
        "${X:-`touch pwned`}",
        "${A#$(touch pwned)}",
        "$((`touch pwned`))",
    ]
    for template in templates:
        result = expand(template, {"A": "a"})
        assert "touch pwned" in result or result == "a"
        with pytest.raises(ExpansionError):
            expand(template, {"A": "a"}, safe=True)
    assert not marker.exists()


def test_values_are_never_re_expanded() -> None:
    assert expand("$b $a", ENV) == "${A} \\"
    assert expand("${B:-$b}", ENV) == "${A}"


@pytest.mark.parametrize("opener", ["${", "${A:-", "${A#", "${A:-${B#"])
def test_pathological_nesting_is_a_syntax_error_not_a_crash(opener: str) -> None:
    with pytest.raises(ExpansionError):
        expand(opener * 5000, {})
    with pytest.raises(ExpansionError):
        list_vars(opener * 5000)


def test_large_templates_expand_in_linear_time() -> None:
    template = "x ${A:-d} $B \\$ " * 50_000
    start = time.perf_counter()
    result = expand(template, {"A": "v"})
    assert result.count("v") == 50_000
    assert time.perf_counter() - start < 10


def test_long_values_with_patterns_stay_fast() -> None:
    value = "ab" * 20_000
    start = time.perf_counter()
    assert expand("${V##*b}", {"V": value}) == ""
    assert expand("${V%%a*}", {"V": value}) == ""
    assert expand("${V#*[!ab]}", {"V": value}) == value
    assert time.perf_counter() - start < 10


@pytest.mark.parametrize("seed", range(3))
def test_escape_survives_random_text(seed: int) -> None:
    rng = random.Random(100 + seed)
    for _ in range(500):
        text = random_template(rng)
        assert expand(escape(text), ENV, strict=True, safe=True) == text
