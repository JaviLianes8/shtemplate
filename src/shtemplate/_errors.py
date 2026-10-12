"""Errors raised while parsing or expanding a template.

Every error is an :class:`ExpansionError`, which is a :class:`ValueError`, so a
single ``except ExpansionError`` (or ``except ValueError``) catches them all.
Each error records the zero-based ``position`` in the template where the
offending construct starts.
"""

from __future__ import annotations


class ExpansionError(ValueError):
    """A template is malformed or a required variable is unset.

    Attributes:
        position: Zero-based index into the template of the construct that
            failed, or ``None`` when no single position applies.
    """

    def __init__(self, message: str, position: int | None = None) -> None:
        super().__init__(message)
        self.position = position


class TemplateSyntaxError(ExpansionError):
    """The template cannot be parsed.

    Raised for an unterminated ``${``, an invalid or unsupported parameter name
    such as ``${}`` or ``${1}``, an unknown operator such as ``${X@y}``, an
    unterminated quote inside a pattern, or nesting deeper than the parser allows.
    """


class UnsetVariableError(ExpansionError):
    """Strict mode met a reference to a variable that is not set.

    Attributes:
        name: The variable name.
    """

    def __init__(self, name: str, position: int) -> None:
        super().__init__(f"undefined variable: {name} (at position {position})", position)
        self.name = name


class ParameterError(ExpansionError):
    """A ``${NAME:?word}`` or ``${NAME?word}`` expansion found its variable missing.

    The message is ``"NAME: word"``, or the shell's default text when ``word``
    is empty.

    Attributes:
        name: The variable name.
        detail: The expanded ``word`` (or the default text), without the name.
    """

    def __init__(self, name: str, detail: str, position: int) -> None:
        super().__init__(f"{name}: {detail}", position)
        self.name = name
        self.detail = detail


class UnsafeTemplateError(ExpansionError):
    """Safe mode rejected the template or stopped an oversized expansion.

    Raised for command substitution (``$(...)``), backquotes and arithmetic
    expansion (``$((...))``), none of which is ever executed, and when the output
    would exceed the configured ``max_output``.
    """
