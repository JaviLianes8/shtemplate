# shtemplate

POSIX shell parameter expansion (`$VAR`, `${VAR:-default}`, `${VAR%pattern}`, ...) over
any mapping, with a command line tool. Typed, safe for untrusted templates, zero dependencies.

Outputs are cross-checked against `dash` and `bash --posix` on a corpus of more than 1,600
templates. Nothing in a template is ever executed.

## Install

```
pip install shtemplate
```

## Usage

```python
from shtemplate import expand

values = {"USER": "ada", "HOME": "/home/ada", "FILE": "report.tar.gz", "EMPTY": ""}

expand("$HOME/${APP:-demo}", values)  # "/home/ada/demo"
expand("${EMPTY:-guest} [${EMPTY-guest}]", values)  # "guest []"
expand("${USER:+signed in as $USER}", values)  # "signed in as ada"
expand("${CONF:-${XDG:-$HOME/.config}}/app", values)  # "/home/ada/.config/app"

# Pattern removal and length
expand("${FILE%.gz} ${FILE%%.*} ${FILE#*.} ${FILE##*.}", values)  # "report.tar report tar.gz gz"
expand("${#USER}", values)  # "3"

# Required values raise a typed error that names the variable
expand("${TOKEN:?token is required}", values)  # ParameterError: TOKEN: token is required

# Escapes: \$ and $$ are a literal dollar
expand("price \\$5 or $$5", values)  # "price $5 or $5"
```

`env` is any `Mapping[str, str]` and is never mutated. It defaults to an empty mapping, so
nothing is read from the process environment unless you pass `os.environ` yourself.

### Strict and safe modes

```python
from shtemplate import expand

expand("$MISSING", {}, strict=True)  # UnsetVariableError: undefined variable: MISSING ...
expand("${MISSING:-ok}", {}, strict=True)  # "ok": the default handles the unset case

expand("$(rm -rf ~)", {})  # "$(rm -rf ~)": left as literal text, never run
expand("$(rm -rf ~)", {}, safe=True)  # UnsafeTemplateError: command substitution ...
```

`strict=True` behaves like `set -u`. `safe=True` is meant for templates you do not trust: it
rejects `$(...)`, `$((...))` and backquotes, caps the output at one million characters
(`max_output=` to change it) and bounds pattern matching work to match.

### Inspecting and escaping

```python
from shtemplate import escape, expand, list_vars

list_vars("$HOME/${APP:-demo}/${LOG:-$HOME/log}")  # ["HOME", "APP", "LOG"]
expand(escape("cost: $5"), {})  # "cost: $5"
```

### Assignment

`${NAME:=word}` and `${NAME=word}` substitute `word` and make it visible to later references
in the same template. The mapping you pass is read-only to `shtemplate`; collect the
assignments with `assigned=` (pass the same dict as `env` to update it in place).

```python
from shtemplate import expand

sink: dict[str, str] = {}
expand("${PORT:=8080} on $PORT", {}, assigned=sink)  # "8080 on 8080"; sink == {"PORT": "8080"}
```

### Supported forms

| Form | Result |
| --- | --- |
| `${NAME}` | the value; empty if unset (an error in strict mode) |
| `$NAME` | same, using the longest valid name |
| `${NAME:-word}` | `word` if unset or empty |
| `${NAME-word}` | `word` if unset |
| `${NAME:=word}` | `word` if unset or empty, and assign it |
| `${NAME=word}` | `word` if unset, and assign it |
| `${NAME:+word}` | `word` if set and not empty, else empty |
| `${NAME+word}` | `word` if set, else empty |
| `${NAME:?word}` | raise `ParameterError` if unset or empty |
| `${NAME?word}` | raise `ParameterError` if unset |
| `${#NAME}` | the length in characters |
| `${NAME%word}` | remove the shortest suffix matching the pattern `word` |
| `${NAME%%word}` | remove the longest matching suffix |
| `${NAME#word}` | remove the shortest matching prefix |
| `${NAME##word}` | remove the longest matching prefix |
| `$$` | a literal `$` |
| `\$NAME` | a literal `$NAME` (backslash also escapes backquote and backslash) |

`word` is expanded only when it is needed, so it may contain other expansions. Patterns use
shell notation: `*`, `?`, `[a-z]`, `[!...]`, `[[:alpha:]]` and backslash or quotes for literal
characters. Malformed templates raise `TemplateSyntaxError` with the position. Every error is an
`ExpansionError`, which is a `ValueError`. The [GUIDE](GUIDE.md) covers the exact rules, the
design decisions and the differences from the shell and from `string.Template`.

## Command line

```
echo 'Hello ${USER:-world}' | shtemplate
shtemplate config.tpl -o config.ini
shtemplate -i --env-file prod.env --set PORT=8080 config.tpl
shtemplate --strict --safe untrusted.tpl
shtemplate --list-vars config.tpl
```

Variables come from the process environment, then each `--env-file` (`NAME=VALUE` lines, never
expanded), then each `--set`. `-i` starts from an empty environment. Errors go to stderr with
exit status 1. `python -m shtemplate` works too.

## Why

Python's `string.Template` understands `$NAME` and `${NAME}` only: no defaults, no required
values, no pattern removal. `os.path.expandvars` silently leaves unknown names in place and
reads only `os.environ`. `shtemplate` gives you the shell's full parameter expansion as a pure
function over a mapping you choose, with typed errors, a strict mode, a safe mode for
untrusted input and a CLI that does what `envsubst` does, plus defaults, required values and
pattern removal.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
