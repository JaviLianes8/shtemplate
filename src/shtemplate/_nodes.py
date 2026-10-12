"""Node types produced by the parser and consumed by the evaluator."""

from __future__ import annotations

from dataclasses import dataclass, field

NAME_START = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
NAME_REST = NAME_START | frozenset("0123456789")
PATTERN_OPS = frozenset({"#", "##", "%", "%%"})


@dataclass(frozen=True)
class Text:
    """Literal characters. ``quoted`` marks pattern characters that match literally."""

    value: str
    quoted: bool = False


@dataclass(frozen=True)
class Param:
    """One ``$NAME`` or ``${...}`` expansion.

    ``op`` is ``""`` (plain), ``"len"``, one of ``- = ? +`` or a pattern operator.
    ``quoted`` marks an expansion whose result must match literally in a pattern.
    """

    name: str
    position: int
    op: str = ""
    colon: bool = False
    word: tuple[Node, ...] = ()
    quoted: bool = False


Node = Text | Param


@dataclass(frozen=True)
class Parsed:
    """A parsed template plus the positions of constructs that are never executed."""

    nodes: tuple[Node, ...]
    unsafe: tuple[tuple[int, str], ...] = field(default=())


def merge(nodes: list[Node]) -> tuple[Node, ...]:
    merged: list[Node] = []
    for node in nodes:
        last = merged[-1] if merged else None
        if isinstance(node, Text) and isinstance(last, Text) and last.quoted == node.quoted:
            merged[-1] = Text(last.value + node.value, node.quoted)
        else:
            merged.append(node)
    return tuple(merged)
