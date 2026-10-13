# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-10-13

### Changed

- The excerpt of the POSIX standard is no longer committed or shipped in the sdist: the
  cited example pairs stay in the tests, and `scripts/fetch_upstream.py` fetches the page,
  checked against `tests/upstream/MANIFEST.json`, for the tests that prove each pair is on it.

## [0.2.0]

### Added

- `${#NAME}` length and the pattern removals `${NAME%word}`, `${NAME%%word}`,
  `${NAME#word}` and `${NAME##word}` with shell pattern matching notation: `*`, `?`,
  bracket expressions with ranges, negation and character classes, and quoting.
- `${NAME:=word}` and `${NAME=word}`: the assigned value is visible to later references in
  the same template; the mapping is never mutated. The new `assigned=` argument collects
  the assignments.
- Nested words: the word of an operator is expanded when needed (`${A:-${B:-x}}`), and the
  closing brace is found by recursive scanning, honouring quotes and `\}`.
- Backslash escapes with here-document rules: `\$`, `` \` ``, `\\` and line continuation.
- Typed errors with a `position`: `TemplateSyntaxError`, `UnsetVariableError`,
  `ParameterError` and `UnsafeTemplateError`, all subclasses of `ExpansionError`.
- `safe=True` for untrusted templates: rejects `$(...)`, `$((...))` and backquotes and caps
  the output size; `max_output=` sets the cap explicitly.
- `list_vars()` lists the referenced names without expanding; `escape()` turns any text into
  a template that expands to it.
- The `shtemplate` command (also `python -m shtemplate`): expands a file or stdin against the
  environment, `--env-file` files and `--set` values, with `--strict`, `--safe`,
  `--list-vars`, `-i` and `-o`.
- GUIDE.md with the exact rules, the design decisions and the differences from the shell and
  from `string.Template`.
- A corpus of more than 1,600 templates checked against dash and bash --posix.

### Changed (breaking)

These change the output of some 0.1.0 templates, most visibly ones with a backslash before
`$` (such as Windows paths) or a `$` inside an operator word.

- The word of `:-`, `-`, `:+`, `+`, `:?` and `?` is now expanded as in the shell
  (`${X:-$HOME/bin}` uses the value of `HOME`). In 0.1.0 it was taken literally; write
  `\$` for a literal dollar inside a word.
- A backslash before `$`, backquote or backslash is now an escape, as in the shell.
- `strict=True` now also applies to `${#NAME}` and the pattern removals, like `set -u`.
- The `:?` message is now `NAME: message`, as the shell prints it.

## [0.1.0]

- Add `expand`: POSIX shell-style expansion of `$VAR` and `${VAR}` over a mapping.
- Support the `:-`, `-`, `:+`, `+`, `:?` and `?` operators and the `$$` literal.
- Add an opt-in strict mode that raises on an unset plain reference.
- Add `ExpansionError` for malformed templates and required variables.
