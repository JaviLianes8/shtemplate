"""Reproduce captured output with a locally installed Bash reference."""

from __future__ import annotations

import os
import random

import oracle
import pytest
from test_oracle import CORPUS, ours


@pytest.mark.skipif(not os.environ.get("SHTEMPLATE_BASH"), reason="set SHTEMPLATE_BASH")
def test_live_bash_reproduces_the_recorded_corpus() -> None:
    cases = [(case["template"], CORPUS["env"], case["strict"]) for case in CORPUS["cases"]]
    results = oracle.run_shell("bash", cases)
    assert [list(result) for result in results] == [case["bash"] for case in CORPUS["cases"]]


@pytest.mark.skipif(not os.environ.get("SHTEMPLATE_BASH"), reason="set SHTEMPLATE_BASH")
def test_live_bash_agrees_on_seeded_operator_combinations() -> None:
    rng = random.Random(20261103)
    cases: list[oracle.Case] = []
    for _ in range(400):
        env = {"A": rng.choice(["", "abc", "xyz"])} if rng.randrange(2) else {}
        operator = rng.choice(["-", ":-", "+", ":+", "=", ":=", "?", ":?"])
        template = "${A" + operator + "${B:-fallback}}:$A"
        cases.append((template, env, bool(rng.randrange(2))))
    results = oracle.run_shell("bash", cases)
    assert [ours(template, dict(env), strict) for template, env, strict in cases] == [
        list(result) for result in results
    ]
