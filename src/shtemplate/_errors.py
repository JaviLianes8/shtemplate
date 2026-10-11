"""Errors raised while expanding a template."""

from __future__ import annotations


class ExpansionError(ValueError):
    """A template is malformed or a required variable is unset."""
