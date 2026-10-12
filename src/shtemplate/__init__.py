"""POSIX shell-style string expansion over any mapping, typed and zero-dependency.

>>> from shtemplate import expand
>>> expand("$HOME/${APP:-demo}", {"HOME": "/home/ada"})
'/home/ada/demo'
"""

from __future__ import annotations

from ._core import expand
from ._errors import (
    ExpansionError,
    ParameterError,
    TemplateSyntaxError,
    UnsafeTemplateError,
    UnsetVariableError,
)
from ._tools import escape, list_vars

__version__ = "0.2.0"

__all__ = [
    "ExpansionError",
    "ParameterError",
    "TemplateSyntaxError",
    "UnsafeTemplateError",
    "UnsetVariableError",
    "escape",
    "expand",
    "list_vars",
]
