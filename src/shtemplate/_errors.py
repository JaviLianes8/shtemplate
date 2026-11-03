"""Errors raised while parsing or expanding a template.

Every error is an :class:`ExpansionError`, which is a :class:`ValueError`, so a
single ``except ExpansionError`` (or ``except ValueError``) catches them all.
Each error records the zero-based ``position`` of the offending construct, or
``None`` when no single position applies, including output and pattern-work limits.
"""

from __future__ import annotations


class ExpansionError(ValueError):
    """A template is malformed or a required variable is unset.

    Attributes:
        position: Zero-based index into the template of the construct that
            failed, or ``None`` when no single position applies.

    >>> ExpansionError("invalid template", 2).position
    2
    """

    def __init__(self, message: str, position: int | None = None) -> None:
        super().__init__(message)
        self.position = position


class TemplateSyntaxError(ExpansionError):
    """The template cannot be parsed.

    Raised for an unterminated ``${``, an invalid or unsupported parameter name
    such as ``${}`` or ``${1}``, an unknown operator such as ``${X@y}``, an
    unterminated quote inside a pattern, or nesting deeper than the parser allows.

    >>> from shtemplate import expand
    >>> try:
    ...     expand("${}")
    ... except TemplateSyntaxError as error:
    ...     print(error.position)
    0
    """


class UnsetVariableError(ExpansionError):
    """Strict mode met a reference to a variable that is not set.

    Attributes:
        name: The variable name.

    >>> str(UnsetVariableError("PORT", 0))
    'undefined variable: PORT (at position 0)'
    """

    def __init__(self, name: str, position: int) -> None:
        label = name if len(name) <= 80 else "<name omitted>"
        super().__init__(f"undefined variable: {label} (at position {position})", position)
        self.name = name


class ParameterError(ExpansionError):
    """A ``${NAME:?word}`` or ``${NAME?word}`` expansion found its variable missing.

    The message omits the expanded word, which can contain credentials.
    Read ``detail`` explicitly when the application needs that sensitive value.

    Attributes:
        name: The variable name.
        detail: The expanded ``word`` (or the default text), without the name.

    >>> error = ParameterError("PORT", "configure a port", 0)
    >>> str(error), error.detail
    ('PORT: required parameter is missing', 'configure a port')
    """

    def __init__(self, name: str, detail: str, position: int) -> None:
        label = name if len(name) <= 80 else "<name omitted>"
        super().__init__(f"{label}: required parameter is missing", position)
        self.name = name
        self.detail = detail


class UnsafeTemplateError(ExpansionError):
    """Safe mode rejected the template or stopped an oversized expansion.

    Raised for command substitution (``$(...)``), backquotes and arithmetic
    expansion (``$((...))``), none of which is ever executed, and when the output
    would exceed the configured ``max_output``.

    >>> from shtemplate import expand
    >>> try:
    ...     expand("$(id)", safe=True)
    ... except UnsafeTemplateError as error:
    ...     print(error.position)
    0
    """
