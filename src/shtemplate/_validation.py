"""Validate public arguments and normalize scalar subclasses."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping


def text_value(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    return str.__str__(value)


def options(
    env: Mapping[str, str] | None,
    assigned: MutableMapping[str, str] | None,
    strict: bool,
    safe: bool,
    max_output: int | None,
) -> int | None:
    if env is not None and not isinstance(env, Mapping):
        raise TypeError("env must be a mapping or None")
    if assigned is not None and not isinstance(assigned, MutableMapping):
        raise TypeError("assigned must be a mutable mapping or None")
    if not isinstance(strict, bool):
        raise TypeError("strict must be a boolean")
    if not isinstance(safe, bool):
        raise TypeError("safe must be a boolean")
    if max_output is not None:
        if isinstance(max_output, bool) or not isinstance(max_output, int):
            raise TypeError("max_output must be an integer or None")
        max_output = int.__int__(max_output)
        if max_output < 0:
            raise ValueError("max_output must be non-negative")
    return max_output
