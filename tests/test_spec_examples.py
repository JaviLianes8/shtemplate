"""The informative examples of POSIX.1-2024 section 2.6.2, run through ``expand``.

Every (command, output) pair below is copied from
https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html as
fetched on 2026-10-12; the verbatim excerpt lives in
``tests/data/posix_2_6_2_examples.txt`` and the first test proves each pair is
in it. The assignments that set up each example are translated by hand into the
``env`` mapping, and the ``echo`` argument becomes the template.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shtemplate import ParameterError, expand

EXCERPT = (Path(__file__).parent / "data" / "posix_2_6_2_examples.txt").read_text("utf-8")

# (setup lines, echo line, output line, env used for expand)
EXAMPLES: list[tuple[str, str, str, dict[str, str]]] = [
    ("foo=asdf", "echo ${foo-bar}xyz}", "asdfxyz}", {"foo": "asdf"}),
    ("foo=", "echo ${foo-bar}xyz}", "xyz}", {"foo": ""}),
    ("unset foo", "echo ${foo-bar}xyz}", "barxyz}", {}),
    ("unset X", "echo ${X:=abc}", "abc", {}),
    ("HOME=/usr/posix", "echo ${#HOME}", "10", {"HOME": "/usr/posix"}),
    ("x=file.c", "echo ${x%.c}.o", "file.o", {"x": "file.c"}),
    ("x=posix/src/std", "echo ${x%%/*}", "posix", {"x": "posix/src/std"}),
    ("x=$HOME/src/cmd", "echo ${x#$HOME}", "/src/cmd", {"x": "/h/src/cmd", "HOME": "/h"}),
    ("x=/one/two/three", "echo ${x##*/}", "three", {"x": "/one/two/three"}),
]


def test_every_example_is_copied_from_the_fetched_excerpt() -> None:
    lines = EXCERPT.splitlines()
    for setup, command, output, _ in EXAMPLES:
        index = lines.index(command, lines.index(setup))
        assert lines[index + 1] == output


@pytest.mark.parametrize(("setup", "command", "output", "env"), EXAMPLES)
def test_spec_example(setup: str, command: str, output: str, env: dict[str, str]) -> None:
    assert expand(command.removeprefix("echo "), env) == output


def test_spec_colon_question_example_message() -> None:
    assert "echo ${posix:?}" in EXCERPT
    assert "sh: posix: parameter null or not set" in EXCERPT
    with pytest.raises(ParameterError) as caught:
        expand("${posix:?}", {})
    assert str(caught.value) == "posix: parameter null or not set"


def test_spec_quoted_asterisk_is_literal_in_a_pattern() -> None:
    assert '${x#"*"}' in EXCERPT and '"${x#*}"' in EXCERPT
    assert expand('${x#"*"}', {"x": "*star"}) == "star"
    assert expand('${x#"*"}', {"x": "plain"}) == "plain"
    assert expand("${x#*}", {"x": "plain"}) == "plain"
    assert expand("${x##*}", {"x": "plain"}) == ""


def test_positional_examples_are_out_of_scope() -> None:
    # The excerpt's ${1}, ${10} and ${3:+posix} examples use positional
    # parameters, which a mapping does not have: ${1} is rejected as a syntax
    # error and a bare $1 stays literal text.
    assert "echo ${3:+posix}" in EXCERPT
    assert expand("$10", {}) == "$10"
