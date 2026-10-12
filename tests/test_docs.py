"""The examples in README.md and the comparison table in GUIDE.md stay true."""

from __future__ import annotations

import ast
import re
import string
from pathlib import Path

import pytest

import shtemplate
from shtemplate import ExpansionError, expand

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text("utf-8")
GUIDE = (ROOT / "GUIDE.md").read_text("utf-8")


def readme_examples() -> list[tuple[str, str, str]]:
    """Return (setup code, expression, claimed result) for each commented README line."""
    found = []
    for block in re.findall(r"```python\n(.*?)```", README, flags=re.DOTALL):
        setup: list[str] = []
        for line in block.splitlines():
            code, _, comment = line.partition("  # ")
            if comment and code.startswith("expand("):
                found.append(("\n".join(setup), code, comment))
            elif code.strip() and not code.startswith(("expand(", "list_vars(")):
                setup.append(code)
    return found


@pytest.mark.parametrize(("setup", "code", "claim"), readme_examples())
def test_readme_example(setup: str, code: str, claim: str) -> None:
    scope: dict[str, object] = {}
    exec(setup, vars(shtemplate).copy(), scope)
    try:
        result = eval(code, {**vars(shtemplate), **scope})
    except ExpansionError as exc:
        assert claim.startswith(type(exc).__name__)
        assert claim.split(": ", 1)[1].rstrip(". ") in f"{exc}"
        return
    literal = re.match(r'"(?:[^"\\]|\\.)*"', claim)
    assert literal is not None, claim
    assert result == ast.literal_eval(literal.group(0))


def test_readme_has_examples() -> None:
    assert len(readme_examples()) >= 12


@pytest.mark.parametrize(
    ("template", "substitute", "safe", "ours"),
    [
        ("$x", "X", "X", "X"),
        ("$xy", KeyError, "$xy", ""),
        ("$$", "$", "$", "$"),
        ("price $5", ValueError, "price $5", "price $5"),
        ("${x:-d}", ValueError, "${x:-d}", "X"),
        ("\\$x", "\\X", "\\X", "$x"),
    ],
)
def test_guide_string_template_table(
    template: str, substitute: object, safe: str, ours: str
) -> None:
    values = {"x": "X"}
    if isinstance(substitute, type):
        with pytest.raises(substitute):
            string.Template(template).substitute(values)
    else:
        assert string.Template(template).substitute(values) == substitute
    assert string.Template(template).safe_substitute(values) == safe
    assert expand(template, values) == ours
    assert f"`{template}`" in GUIDE
