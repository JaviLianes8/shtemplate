# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/shtemplate/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.

The POSIX page behind the spec examples is not committed. Fetch it with
`python scripts/fetch_upstream.py`; until then the tests that read it skip.

## Shell oracle

`tests/data/oracle_corpus.json` records what dash and bash --posix print for each corpus
template. Rebuild it with `python scripts/build_corpus.py` (needs WSL with dash) after
changing the generator or the hand-written cases in `scripts/corpus_cases.py`.
`scripts/e2e_wheel.py` builds the wheel, installs it in a throwaway virtual environment and
drives the installed `shtemplate` command.
