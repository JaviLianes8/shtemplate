# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-02

### Stable

- The eight public names, keyword-only expansion options, mapping isolation,
  lazy operator words, assignment collection and command line interface are stable.
- Python 3.10 through 3.14, including free-threaded 3.14; no runtime dependencies.

### Changed

- `ParameterError` messages now say `NAME: required parameter is missing` instead
  of printing the expanded word, which can contain secrets. The complete word is
  still available explicitly as `error.detail`, including default shell messages.
- Error messages omit variable names longer than 80 characters; `error.name`
  retains the complete name. CLI usage and invalid `--set` diagnostics no longer
  echo arguments, which can contain credentials.
- `max_output` now rejects booleans and non-integers with `TypeError`, and negative
  integers with `ValueError`, consistently even for empty templates.
- Text arguments, mapping arguments, boolean options and fetched environment values
  now consistently reject invalid types with `TypeError`, including a fetched `None`.
  Unused environment values remain unevaluated. String and integer subclasses use
  their underlying base values without overridden conversions or length comparisons.
- CLI filesystem diagnostics omit paths longer than 200 characters and use bounded
  system error descriptions. Env-file and UTF-8 source labels use the same path bound.

### Fixed

- Malformed patterns containing repeated unclosed brackets or character classes
  are scanned in linear time rather than repeatedly scanning their remaining tail.
- The pattern work limit counts all pattern characters, including bracket members,
  before compilation; long bracket expressions can now reach the limit earlier.
- Collating symbols work as either endpoint of a bracket range, including mixed
  character/symbol endpoints and all four pattern-removal operators.
- Assignment expansions substitute the value after quote removal; quoting on the
  enclosing expansion still controls whether pattern metacharacters are literal.
- Double-quoted pattern words retain a backslash before `}`, including nested words.
- Apostrophe runs are parsed without repeatedly scanning the remaining template.
- Cumulative output limits stop evaluation before further siblings allocate values;
  failed expansions still leave the assignment sink unchanged.
- String subclasses cannot bypass safe output limits, integer subclasses cannot
  override budget comparisons, and unhashable string templates work with parser caching.

### Added

- Runnable examples for every public error, stronger privacy and boundary contracts,
  current specification checks, and installed-wheel upgrade checks from 0.2.1.
- Exact safe-output and pattern-work boundaries, unknown error positions, empty default
  environments, repeated `--set` precedence, source precedence and `--list-vars -o`
  subprocess contracts.
- Read-only assignment sink rejection, mutable mapping acceptance, exact 200/201-character
  diagnostic path boundaries, and long-path UTF-8 and dotenv error contracts.
- Documentation clarifies nested parameter evaluation in command-like text, optional
  error positions, NUL limits of shell transport and the verified Bash backslash behavior.


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
