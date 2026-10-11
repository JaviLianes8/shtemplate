"""POSIX shell-style string expansion over any mapping, typed and zero-dependency."""

from __future__ import annotations

from ._core import expand
from ._errors import ExpansionError

__version__ = "0.1.0"

__all__ = ["ExpansionError", "expand"]
