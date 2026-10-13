# shtemplate guide

This guide states exactly what `shtemplate` does, which choices it makes where the shell
standard leaves room, and how it differs from a real shell and from `string.Template`.

The reference is POSIX.1-2024, Shell Command Language, section 2.6.2 Parameter Expansion,
section 2.14 Pattern Matching Notation and section 2.2 Quoting:
https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html

## The model: a here-document body

A template is read the way a POSIX shell reads the body of an unquoted here-document
(`cat <<EOF`). That is the context where a shell expands parameters in free text without
splitting words or globbing, so it is the natural meaning of "shell-style template".

At the top level of a template:

- `$NAME` and `${...}` are expanded. Without braces the longest valid name is used, so `$Ab`
  reads `Ab`. A name is an ASCII letter or underscore followed by letters, digits or
  underscores.
- A backslash escapes `$`, backquote, backslash and newline: `\$` is `$`, `\\` is `\`,
  and a backslash before a newline joins the two lines. Before any other character the
  backslash is kept (`\n` stays two characters).
- Single and double quotes are ordinary characters.
- `$$` is a literal `$` (see "Differences from a shell").
- A `$` that does not start a name or a brace stays literal: `$5`, `$ `, `$-`, `$1`.

## Operators

| Operator | Set and not empty | Set but empty | Unset |
| --- | --- | --- | --- |
| `${p:-w}` | value | `w` | `w` |
| `${p-w}` | value | empty | `w` |
| `${p:=w}` | value | assign `w` | assign `w` |
| `${p=w}` | value | empty | assign `w` |
| `${p:?w}` | value | error | error |
| `${p?w}` | value | empty | error |
| `${p:+w}` | `w` | empty | empty |
| `${p+w}` | `w` | `w` | empty |

`${#p}` is the length of the value in characters (0 when unset). `${p%w}`, `${p%%w}`,
`${p#w}` and `${p##w}` remove the shortest or longest suffix or prefix that matches the
pattern `w`; when nothing matches the value is unchanged.

The word `w` is expanded only when its value is needed. An unused word may contain a
`${X:?...}` that never fires or an assignment that never happens. Syntax errors are still
reported for the whole template, used or not, because the template is parsed first.

### Words of the defaulting operators

Inside the word of `-`, `=`, `?` and `+` (written in the here-document context):

- `$NAME` and `${...}` expand, and nest to any depth up to 64 levels.
- A backslash escapes `$`, backquote, `"`, `\` and `}`. `${X:-a\}b}` gives `a}b`.
- Double quotes are removed and protect a `}`: `${X:-"x}"y}` gives `x}y`. The standard
  leaves unescaped double quotes here unspecified; dash and bash both behave this way.
- Single quotes are ordinary characters: `${X:-'a'}` gives `'a'`, exactly as the shells do.

### Words of the pattern operators

The standard says the enclosing double quotes have no effect on the four pattern
operators, so their word is read as unquoted shell text:

- `*`, `?` and `[...]` are pattern characters.
- A backslash quotes the next character, single quotes quote their content and double
  quotes quote theirs (with `$` still expanding inside them). Quoted characters match
  themselves: `${V#'*'}` removes a literal star.
- The result of an unquoted `$NAME` inside the pattern is itself a pattern, so
  `${V#$PREFIX}` treats a `*` in `PREFIX` as a wildcard. Write `${V#"$PREFIX"}` to match it
  literally.
- Words nested inside a pattern word follow the same unquoted rules.

If the variable is unset its pattern word is not expanded at all; dash and bash agree.

### Pattern matching notation

- `?` matches one character, `*` any run of characters including none.
- `[abc]`, ranges `[a-z]`, negation with `[!...]` (also `[^...]`, like bash), a leading `]`
  as a member (`[]a]`), character classes `[[:alpha:]]` (`alnum alpha blank cntrl digit
  graph lower print punct space upper xdigit`) and the one-character forms `[=a=]` and
  `[.a.]`. An unknown class matches nothing. A `[` that does not start a valid bracket
  expression matches itself.
- Ranges compare code points. Classes use Python's Unicode string methods, except `digit`,
  `xdigit` and `punct`, which are ASCII, and `blank`, which is space and tab.
- Matching runs as an automaton over all prefixes at once, in
  `O(len(value) * len(pattern))` time. No pattern can make it backtrack exponentially.
  That product can still be large when both sides are long, so whenever `max_output` is set
  (always in safe mode) a removal that would need more than ten times `max_output` steps
  raises `UnsafeTemplateError` before matching starts.

## Decisions where a mapping is not a shell

- **Assignment.** `${p:=w}` and `${p=w}` cannot assign into a read-only mapping, and
  `shtemplate` never mutates the mapping you pass. The assigned value lives in an overlay
  for the rest of the expansion, so `${PORT:=80} $PORT` gives `80 80`, as in a shell. Pass
  `assigned=` to receive the assignments after a successful expansion; it is not touched when
  the expansion fails. Passing the same dict as `env` and `assigned` updates it in place.
- **`:?` and `?`.** A shell prints the message and exits. `shtemplate` raises
  `ParameterError` with `name`, `detail` and `position`; `str(error)` is `NAME: message`, or
  `NAME: parameter null or not set` (`NAME: parameter not set` for `?`) when the word is empty,
  matching dash.
- **Strict mode** is `set -u`: a plain reference, `${#p}` or a pattern removal on an unset
  variable raises `UnsetVariableError`. The defaulting operators still work, and an empty
  value counts as set.
- **Command substitution and arithmetic** (`$(...)`, backquotes, `$((...))`) are never
  executed. By default they are left in the output as literal text. In safe mode they raise
  `UnsafeTemplateError`. Escaped forms (`\$(`, `` \` ``) are plain text in both modes.
- **Safe mode** also caps the output at one million characters (`max_output=` changes it,
  and works without safe mode too). Assignments can double a value at every step, so a short
  template could otherwise produce gigabytes. The same limit bounds pattern matching work, as
  described above, so a few hundred bytes of template cannot keep the matcher busy for hours.
- **Errors carry positions.** Every error has a zero-based `position` into the template:
  the `$` of the failing expansion, or the start of the malformed construct.

## Differences from a shell

These are deliberate. The two that occur in the oracle corpus (`$-` and `${R#"$R"}`) are
listed in `tests/test_oracle.py` with their reasons.

- `$$` is a literal `$`, not a process id. A mapping has no process.
- Positional and special parameters (`$1`, `${10}`, `$@`, `$*`, `$#`, `$?`, `$-`, `$!`,
  `$0`) do not exist in a mapping. Without braces they stay literal text; with braces
  (`${1}`, `${#}`) they are a `TemplateSyntaxError`.
- `${V#"$P"}` matches the value of `P` literally, as POSIX requires and bash does. dash
  still treats a bracket expression or a backslash coming from the quoted value as active.
- `[^...]` negates, as in bash; dash treats `^` as an ordinary member.
- `[[=a=]]` and `[[.a.]]` match `a`, as in bash; dash does not support these forms.
- A backslash just before the closing brace in a word (`${X:-\\}`) is an escaped backslash
  followed by the closing brace. dash and bash both report a syntax error.
- When a variable is set but empty, its pattern word is expanded (POSIX and dash); bash skips
  it.
- Lengths and `?` count characters (Unicode code points), as bash does; dash counts bytes.
- Tilde expansion does not apply: in a here-document a shell leaves `~` alone too.

## Evidence

- `tests/data/oracle_corpus.json`: more than 1,600 templates from `scripts/build_corpus.py`
  (hand-written generation rules with a fixed seed plus hand-written edge cases), with the
  outputs of `dash` and `bash --posix` under WSL. Every case matches dash except `$-` and
  `${R#"$R"}`, the two deviations above that the corpus exercises. A live test sends a fresh seeded batch to dash when WSL is
  available.
- `tests/test_spec_examples.py` runs the informative examples of section 2.6.2, cited from
  the standard; with the page fetched by `scripts/fetch_upstream.py`, it also proves each
  example is on the page.
- `tests/test_fuzz.py` throws random templates at every entry point and checks that only
  `ExpansionError` is raised, that nothing hangs and that no process is ever started.

## Compared with `string.Template`

| Input | `string.Template.substitute` | `safe_substitute` | `shtemplate.expand` |
| --- | --- | --- | --- |
| `$x`, `${x}` (x set) | value | value | value |
| `$xy` (xy unset) | `KeyError` | `$xy` | empty, or `UnsetVariableError` in strict mode |
| `$$` | `$` | `$` | `$` |
| `price $5` | `ValueError` | `price $5` | `price $5` |
| `${x:-d}` | `ValueError` | `${x:-d}` | value of x, or `d` |
| `\$x` | `\` + value | `\` + value | `$x` |
| `${1}` | `ValueError` | `${1}` | `TemplateSyntaxError` |

Both use ASCII names and `$$` for a literal dollar. `string.Template` has no defaults,
required values, conditional text, pattern removal or length, and gives backslash no meaning.
Its identifier and delimiter can be customised by subclassing; `shtemplate` follows the shell
grammar and is not configurable that way.
