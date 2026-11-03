"""Expand a parsed template against a mapping."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping

from ._errors import ParameterError, UnsafeTemplateError, UnsetVariableError
from ._nodes import PATTERN_OPS, Node, Param, Text
from ._parser import parse
from ._pattern import remove
from ._validation import options, text_value

SAFE_MAX_OUTPUT = 1_000_000
WORK_FACTOR = 10
Segment = tuple[str, bool]


def expand(
    template: str,
    env: Mapping[str, str] | None = None,
    *,
    strict: bool = False,
    safe: bool = False,
    assigned: MutableMapping[str, str] | None = None,
    max_output: int | None = None,
) -> str:
    """Expand POSIX shell parameter expansions in ``template`` from ``env``.

    Supported forms: ``$NAME``, ``${NAME}``, ``${#NAME}``, the defaulting
    operators ``:-``, ``-``, ``:=``, ``=``, ``:?``, ``?``, ``:+``, ``+`` and the
    pattern removals ``#``, ``##``, ``%``, ``%%``. Operator words are expanded
    only when needed, so they may nest (``${A:-${B:-x}}``). Backslash escapes
    ``$``, backquote and backslash (``\\$HOME`` stays literal) and ``$$`` is a
    literal dollar. Commands and arithmetic are never executed. Their delimiters
    remain in the output, but parameters inside still expand and may assign or
    raise errors. Safe mode rejects these constructs.

    Args:
        template: The text to expand.
        env: The variables. Defaults to an empty mapping; pass ``os.environ``
            explicitly to read the process environment. Never mutated.
        strict: Behave like ``set -u``: a plain reference, ``${#NAME}`` or a
            pattern removal on an unset variable raises ``UnsetVariableError``.
        safe: For untrusted templates: reject ``$(...)``, ``$((...))`` and
            backquotes with ``UnsafeTemplateError`` and cap the output at
            ``max_output`` (one million characters unless given).
        assigned: If given, receives the values assigned by ``:=`` and ``=``
            after a successful expansion. Pass ``env`` itself to update it.
        max_output: Raise ``UnsafeTemplateError`` if any expansion grows past
            this many characters, or if a pattern removal would need more than
            ten times this many matching steps (value length times pattern
            length), which bounds the time an untrusted template can take.
            Must be a non-negative integer or ``None``; booleans are rejected.

    Returns:
        The expanded string.

    Raises:
        TemplateSyntaxError: The template is malformed.
        UnsetVariableError: Strict mode met an unset variable.
        ParameterError: A ``:?`` or ``?`` expansion found its variable missing.
        UnsafeTemplateError: Safe mode rejected the template or the output limit
            was reached.
        TypeError: Text or fetched values are not strings, mappings or boolean
            options have invalid types, or ``max_output`` is not an integer or
            ``None``. String and integer subclasses use their underlying values.
        ValueError: ``max_output`` is negative.

    Examples:
        >>> expand("${USER:-guest}@${HOST:-localhost}", {"USER": "ada"})
        'ada@localhost'
        >>> expand("${FILE%.*}.o ${#FILE}", {"FILE": "main.c"})
        'main.o 6'
        >>> expand("${URL#*://}", {"URL": "https://example.org"})
        'example.org'
    """
    max_output = options(env, assigned, strict, safe, max_output)
    parsed = parse(template)
    if safe:
        if parsed.unsafe:
            position, kind = parsed.unsafe[0]
            raise UnsafeTemplateError(
                f"{kind} is not allowed in safe mode (at position {position})", position
            )
        if max_output is None:
            max_output = SAFE_MAX_OUTPUT
    evaluator = _Evaluator(env if env is not None else {}, strict, max_output)
    result = evaluator.text(parsed.nodes)
    if assigned is not None:
        assigned.update(evaluator.overlay)
    return result


class _Evaluator:
    def __init__(self, env: Mapping[str, str], strict: bool, max_output: int | None) -> None:
        self.env = env
        self.strict = strict
        self.max_output = max_output
        self.overlay: dict[str, str] = {}

    def lookup(self, name: str) -> str | None:
        if name in self.overlay:
            return self.overlay[name]
        missing = object()
        value = self.env.get(name, missing)
        if value is missing:
            return None
        if not isinstance(value, str):
            raise TypeError("environment values must be strings")
        return text_value(value, "environment values must be strings")

    def _check(self, size: int) -> None:
        if self.max_output is not None and size > self.max_output:
            raise UnsafeTemplateError(
                f"expansion exceeds the limit of {self.max_output} characters"
            )

    def segments(self, nodes: tuple[Node, ...]) -> list[Segment]:
        """Expand ``nodes`` into ``(text, literal)`` pieces; literal pieces match as-is."""
        parts: list[Segment] = []
        size = 0
        for node in nodes:
            if isinstance(node, Text):
                found = [(node.value, node.quoted)]
            else:
                found = self.param(node)
                if node.quoted:
                    found = [(value, True) for value, _ in found]
            size += sum(len(value) for value, _ in found)
            self._check(size)
            parts.extend(found)
        return parts

    def text(self, nodes: tuple[Node, ...]) -> str:
        return "".join(value for value, _ in self.segments(nodes))

    def pattern(self, nodes: tuple[Node, ...]) -> str:
        return "".join(
            "".join("\\" + c for c in value) if literal else value
            for value, literal in self.segments(nodes)
        )

    def _unset(self, node: Param) -> str:
        if self.strict:
            raise UnsetVariableError(node.name, node.position)
        return ""

    def param(self, node: Param) -> list[Segment]:
        value = self.lookup(node.name)
        op = node.op
        if op == "":
            return [(self._unset(node) if value is None else value, False)]
        if op == "len":
            return [(str(len(self._unset(node) if value is None else value)), False)]
        if op in PATTERN_OPS:
            # dash and bash both skip the pattern word of an unset variable.
            if value is None:
                return [(self._unset(node), False)]
            limit = None if self.max_output is None else self.max_output * WORK_FACTOR
            return [(remove(value, self.pattern(node.word), op, limit), False)]
        missing = value is None or (node.colon and value == "")
        if op == "+":
            return [] if missing else self.segments(node.word)
        if not missing:
            return [(value or "", False)]
        if op == "-":
            return self.segments(node.word)
        if op == "=":
            value = self.text(node.word)
            self.overlay[node.name] = value
            return [(value, False)]
        detail = self.text(node.word)
        if not detail:
            detail = "parameter null or not set" if node.colon else "parameter not set"
        raise ParameterError(node.name, detail, node.position)
