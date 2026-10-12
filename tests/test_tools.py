"""list_vars and escape."""

from __future__ import annotations

import random

import pytest

from shtemplate import TemplateSyntaxError, escape, expand, list_vars


def test_list_vars_in_order_of_first_use() -> None:
    template = "$HOME/${APP:-demo}/${#HOME} ${CFG:-${XDG:-$HOME/.config}} ${F%.$EXT}"
    assert list_vars(template) == ["HOME", "APP", "CFG", "XDG", "F", "EXT"]


def test_list_vars_ignores_escaped_and_literal_dollars() -> None:
    assert list_vars("\\$A $$ $1 $(cmd) `x` '$B'") == ["B"]


def test_list_vars_does_not_expand_or_raise_on_required() -> None:
    assert list_vars("${TOKEN:?required} ${U:=x}") == ["TOKEN", "U"]


def test_list_vars_rejects_malformed_templates() -> None:
    with pytest.raises(TemplateSyntaxError):
        list_vars("${A")


def test_escape_examples() -> None:
    assert escape("cost: $5") == "cost: \\$5"
    assert escape("a\\b`c") == "a\\\\b\\`c"
    assert escape("plain") == "plain"


@pytest.mark.parametrize("seed", range(5))
def test_escape_round_trips_any_text(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = "ab$\\`{}'\"#%:-=?+*[]!\n é"
    for _ in range(300):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 20)))
        assert expand(escape(text), {"a": "X"}) == text
        assert list_vars(escape(text)) == []


def test_escaped_text_inside_a_template() -> None:
    literal = "price: $9.99"
    assert expand(f"{escape(literal)} for $WHO", {"WHO": "you"}) == "price: $9.99 for you"
