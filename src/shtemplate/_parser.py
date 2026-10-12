"""Parse a template into literal text and parameter-expansion nodes.

The template is read like the body of an unquoted shell here-document: only
``$``, backquote and backslash are special at the top level. Operator words are
read with the rules of POSIX.1-2024 2.6.2 and 2.2.3, so the closing brace is
found by recursive scanning and quotes inside a word are honoured.
"""

from __future__ import annotations

from functools import lru_cache

from ._errors import TemplateSyntaxError
from ._nodes import NAME_REST, NAME_START, PATTERN_OPS, Node, Param, Parsed, Text, merge

MAX_DEPTH = 64
_WORD_ESCAPES = frozenset('$`"\\}')
_TOP_ESCAPES = frozenset("$`\\")


@lru_cache(maxsize=512)
def parse(template: str) -> Parsed:
    """Parse ``template``; raise :class:`TemplateSyntaxError` when it is malformed."""
    parser = _Parser(template)
    nodes = parser.top()
    return Parsed(nodes, tuple(parser.unsafe))


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.depth = 0
        self.unsafe: list[tuple[int, str]] = []

    def _peek(self, offset: int = 0) -> str:
        index = self.pos + offset
        return self.text[index] if index < len(self.text) else ""

    def top(self) -> tuple[Node, ...]:
        nodes: list[Node] = []
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char == "\\" and self._peek(1) in _TOP_ESCAPES and self._peek(1):
                nodes.append(Text(self._peek(1)))
                self.pos += 2
            elif char == "\\" and self._peek(1) == "\n":
                self.pos += 2
            elif char == "$":
                nodes.append(self._dollar(quoted=False, unquoted=False))
            else:
                if char == "`":
                    self.unsafe.append((self.pos, "backquote command substitution"))
                nodes.append(Text(char))
                self.pos += 1
        return merge(nodes)

    def _read_name(self) -> str:
        start = self.pos
        if self._peek() and self._peek() in NAME_START:
            self.pos += 1
            while self._peek() and self._peek() in NAME_REST:
                self.pos += 1
        return self.text[start : self.pos]

    def _dollar(self, quoted: bool, unquoted: bool) -> Node:
        start = self.pos
        nxt = self._peek(1)
        if nxt == "{":
            return self._braced(start, quoted, unquoted)
        if nxt and nxt in NAME_START:
            self.pos += 1
            return Param(self._read_name(), start, quoted=quoted)
        if nxt == "$":
            self.pos += 2
            return Text("$", quoted)
        if nxt == "(":
            kind = "arithmetic expansion" if self._peek(2) == "(" else "command substitution"
            self.unsafe.append((start, kind))
        self.pos += 1
        return Text("$", quoted)

    def _error(self, message: str, position: int) -> TemplateSyntaxError:
        return TemplateSyntaxError(f"{message} at position {position}", position)

    def _braced(self, start: int, quoted: bool, unquoted: bool) -> Param:
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise self._error(f"expansions nested deeper than {MAX_DEPTH}", start)
        self.pos += 2
        if self._peek() == "#" and self._peek(1) in NAME_START and self._peek(1):
            self.pos += 1
            name = self._read_name()
            if self._peek() != "}":
                raise self._error("invalid length expansion", start)
            self.pos += 1
            self.depth -= 1
            return Param(name, start, "len", quoted=quoted)
        name = self._read_name()
        if not name:
            if not self._peek():
                raise self._error("unterminated expansion: missing '}'", start)
            raise self._error("invalid variable name in expansion", start)
        op, colon = self._operator(start)
        word: tuple[Node, ...] = ()
        if op:
            word = self._word(unquoted or op in PATTERN_OPS, start)
        self.depth -= 1
        return Param(name, start, op, colon, word, quoted)

    def _operator(self, start: int) -> tuple[str, bool]:
        char = self._peek()
        if char == "}":
            self.pos += 1
            return "", False
        if not char:
            raise self._error("unterminated expansion: missing '}'", start)
        colon = char == ":"
        if colon:
            self.pos += 1
            char = self._peek()
        if char and char in "-=?+":
            self.pos += 1
            return char, colon
        if not colon and char in "#%":
            double = self._peek(1) == char
            self.pos += 2 if double else 1
            return char * 2 if double else char, False
        if not char:
            raise self._error("unterminated expansion: missing '}'", start)
        raise self._error(f"unknown operator {char!r} in expansion", start)

    def _word(self, unquoted: bool, start: int) -> tuple[Node, ...]:
        nodes: list[Node] = []
        in_dq = False
        while True:
            char = self._peek()
            if not char:
                raise self._error("unterminated expansion: missing '}'", start)
            if char == "}" and not in_dq:
                self.pos += 1
                return merge(nodes)
            literal = unquoted and in_dq
            if char == "\\":
                nodes.extend(self._escape(unquoted, in_dq, start))
            elif char == '"':
                in_dq = not in_dq
                self.pos += 1
            elif char == "'" and unquoted and not in_dq:
                nodes.append(Text(self._single_quoted(start), True))
            elif char == "$":
                nodes.append(self._dollar(literal, unquoted and not in_dq))
            else:
                if char == "`":
                    self.unsafe.append((self.pos, "backquote command substitution"))
                nodes.append(Text(char, literal))
                self.pos += 1

    def _escape(self, unquoted: bool, in_dq: bool, start: int) -> list[Node]:
        nxt = self._peek(1)
        if not nxt:
            raise self._error("unterminated expansion: missing '}'", start)
        if nxt == "\n":
            self.pos += 2
            return []
        if unquoted and not in_dq:
            self.pos += 2
            return [Text(nxt, True)]
        if nxt in _WORD_ESCAPES:
            self.pos += 2
            return [Text(nxt, unquoted)]
        self.pos += 1
        return [Text("\\", unquoted)]

    def _single_quoted(self, start: int) -> str:
        end = self.text.find("'", self.pos + 1)
        if end == -1:
            raise self._error("unterminated single quote", start)
        content = self.text[self.pos + 1 : end]
        self.pos = end + 1
        return content
