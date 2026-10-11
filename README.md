# shtemplate

POSIX shell-style string expansion over any mapping, typed and zero-dependency.

## Install

```
pip install shtemplate
```

## Usage

```python
from shtemplate import expand

values = {"USER": "ada", "HOME": "/home/ada", "EMPTY": ""}

expand("Hello ${USER}", values)              # "Hello ada"
expand("$USER lives in $HOME", values)       # "ada lives in /home/ada"

# ${VAR:-default}: use the default when unset or empty
expand("${ROLE:-guest}", values)             # "guest"
expand("${EMPTY:-guest}", values)            # "guest"

# ${VAR-default}: use the default only when unset, keep an empty value
expand("[${EMPTY-guest}]", values)           # "[]"

# ${VAR:+alt}: use the alternative only when set and non-empty
expand("${USER:+known}", values)             # "known"
expand("${EMPTY:+known}", values)            # ""

# ${VAR:?message}: raise when unset or empty
expand("${TOKEN:?token is required}", values)  # raises ExpansionError

# $$ is a literal dollar
expand("price $$5", values)                  # "price $5"
```

Strict mode turns a plain reference to an unset variable into an error instead of
an empty string. The default and alternative operators still work in strict mode,
since they handle the unset case themselves:

```python
expand("${MISSING}", values, strict=True)        # raises ExpansionError
expand("${MISSING:-ok}", values, strict=True)    # "ok"
```

`env` is any `Mapping[str, str]`. It defaults to an empty mapping, so nothing is
read from the process environment unless you pass `os.environ` yourself.

### Supported forms

| Form | Result |
| --- | --- |
| `${VAR}`, `$VAR` | the value, or empty (or an error in strict mode) if unset |
| `${VAR:-word}` | `word` if `VAR` is unset or empty |
| `${VAR-word}` | `word` if `VAR` is unset |
| `${VAR:+word}` | `word` if `VAR` is set and non-empty |
| `${VAR+word}` | `word` if `VAR` is set |
| `${VAR:?word}` | raise `ExpansionError(word)` if `VAR` is unset or empty |
| `${VAR?word}` | raise `ExpansionError(word)` if `VAR` is unset |
| `$$` | a literal `$` |

A malformed template (an unterminated `${`, an empty name, an unknown operator)
raises `ExpansionError`. The default or alternative word is taken literally and is
not expanded again, so braces inside it are not required.

## Why

Python's `string.Template` understands `$VAR` and `${VAR}` but nothing else: there
is no way to supply a default, require a value, or branch on whether a variable is
set. The shell has done all of this for decades.

`expandvars` covers the same shell syntax, but it is built around the process
environment (its name and its default source are `os.environ`). `shtemplate` is a
pure function over a mapping you pass in: no environment access, no global state,
no side effects, fully typed, and with an opt-in strict mode. Reach for it when you
want shell-style expansion of config strings or templates from an explicit set of
values rather than from the environment.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
