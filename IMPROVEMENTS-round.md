# Improvement round

Progress:
- [x] Brainstorm ranked improvements
- [x] Core: full parameter expansion (2.6.2) with nested words and pattern removal
- [x] Escaping, typed errors with positions, strict and safe modes
- [x] Listing referenced variables and escaping helper
- [x] CLI with [project.scripts]
- [x] Docs: docstrings, GUIDE, README, CHANGELOG, version bump
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Contracts, oracle corpus (dash via WSL), fuzz, wheel e2e
- [ ] Pull request opened
- [ ] Independent review fixed, re-gated, trace guard clean

Ground truth: POSIX.1-2024 Shell Command Language, 2.6.2 Parameter Expansion and
2.14 Pattern Matching Notation, fetched from
https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html.
Oracle: `dash` and `bash --posix` in WSL, template expanded as an unquoted here-document body.

## Ranked ideas

1. Full operator set: `${#p}`, `${p%w}`, `${p%%w}`, `${p#w}`, `${p##w}`, `${p:=w}`, `${p=w}`.
   Pattern matching notation (2.14): `?`, `*`, bracket expressions with ranges, negation and
   character classes, backslash escapes. Linear-time matcher, no regex backtracking blowups.
2. Nested words: the word of an operator is expanded (`${A:-${B:-x}}`, `${X:-$HOME/bin}`), and
   the closing brace is found by recursive scanning, as the standard requires.
3. Escaping with here-document rules: `\$`, `` \` ``, `\`, `\<newline>`, plus `\}` inside braces.
   Keep `$$` as a literal dollar (a mapping has no process id). Add `escape()` so any literal
   text round-trips through `expand()`.
4. Typed errors carrying the position: `TemplateSyntaxError`, `UnsetVariableError` (strict),
   `ParameterError` (`:?`), `UnsafeTemplateError` (safe mode), all `ExpansionError` subclasses.
5. Strict mode matching `set -u`: plain references, `${#p}` and the pattern operators fail on
   an unset name; the defaulting operators keep working.
6. Safe mode for untrusted templates: command substitution, backquotes and arithmetic are
   rejected instead of left literal; output size and nesting depth are bounded.
7. Assignment operators against a read-only mapping: the caller's mapping is never mutated; the
   assigned value is visible to later references in the same template and can be collected
   through an optional `assigned` dict.
8. `list_vars()`: every referenced name in order of appearance, without expanding.
9. CLI: expand stdin or a file against the environment, `.env`-style files and `--set`,
   with `--strict`, `--safe`, `--list-vars`, errors on stderr and exit status 1.
10. Docs: docstrings with examples, GUIDE.md (semantics, decisions, differences from the shell
    and from `string.Template`), README refresh, CHANGELOG.
11. Evidence: contract test over the whole promise, seeded corpus checked against dash, fuzzing
    for no crash, no hang and no execution, wheel installed in a throwaway venv.
