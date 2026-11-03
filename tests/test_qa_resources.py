"""Handwritten contracts for bounded parsing and incremental output checks."""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Iterator, Mapping

import pytest

from shtemplate import UnsafeTemplateError, expand, list_vars


def test_apostrophe_runs_do_not_rescan_the_remaining_template() -> None:
    started = time.perf_counter()
    for size in (8000, 16000, 32000):
        template = "'" * size
        assert expand(template, safe=True) == template
        assert list_vars(template) == []
    assert time.perf_counter() - started < 5


def test_output_limit_stops_before_evaluating_later_siblings() -> None:
    reads: list[str] = []

    class Values(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            reads.append(key)
            if key == "X":
                return "x" * 50
            raise KeyError(key)

        def __iter__(self) -> Iterator[str]:
            return iter(("X",))

        def __len__(self) -> int:
            return 1

    env = Values()
    sink = {"unchanged": "yes"}
    template = "".join("${A" + str(i) + ":=$X$X}" for i in range(128))
    with pytest.raises(UnsafeTemplateError):
        expand(template, env, max_output=100, assigned=sink)
    assert "A2" not in reads
    assert sink == {"unchanged": "yes"}


def test_safe_mode_does_not_retain_every_oversized_sibling_assignment() -> None:
    env = {"X": "x" * 500000}
    template = "".join("${A" + str(i) + ":=$X$X}" for i in range(128))
    tracemalloc.start()
    try:
        with pytest.raises(UnsafeTemplateError):
            expand(template, env, safe=True)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 5_000_000
