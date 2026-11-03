# shtemplate 1.0.0 certification report

Preparation for 1.0.0 from main `617a10d`. PyPI serves 0.2.1.
The release date is 2026-11-02. Evidence was collected on 2026-11-02 UTC
(2026-11-03 local time).

Progress:
- [x] API review, typed errors, examples and strict typing (items 1 to 5)
- [x] Contract tests and seeded fuzzing (items 6 and 9)
- [x] Current POSIX text fetched and real Bash output checked (item 7)
- [x] README, GUIDE, CHANGELOG and distribution metadata (items 11 to 14)
- [x] Final wheel, upgrade and interpreter checks (items 8 and 10)
- [x] Mutation round (item 18)
- [x] Final four gates (item 15)
- [ ] Independent review (item 16)
- [ ] Five independent QA lenses (item 19)
- [ ] Merge and publication (item 17)

## Scorecard

| Item | Result and evidence |
| --- | --- |
| 1 | PASS: stable eight-name API, signatures/defaults retained; changes documented |
| 2 | PASS: exact `__all__` contract; public imports in docs |
| 3 | PASS: 15 doctest examples and executed README examples |
| 4 | PASS: `mypy --strict src tests`, installed `py.typed` |
| 5 | PASS: typed template errors, bounded/redacted diagnostics, documented limits |
| 6 | PASS: all public names, operator states, CLI, errors and boundaries tested |
| 7 | PASS: current POSIX fetch, 1,644 real Bash results and 400 fresh cases |
| 8 | PASS: wheel in a fresh venv, real CLI, PyPI 0.2.1 upgrade |
| 9 | PASS: seeded fuzz, escape properties, large-input and work-limit checks |
| 10 | PASS: all 12 available CPython versions/builds, including embedded and free-threaded |
| 11 | PASS: problem, comparison, quick start, absolute links, strict twine check |
| 12 | PASS: dated 2026-11-02 section listing all changes from 0.2.1 |
| 13 | PASS: 1.0.0, stable classifier, supported versions, license, URLs, no dependencies |
| 14 | PASS: wheel and sdist contents inspected; LICENSE and type marker present |
| 15 | PASS: four gates independently exit 0; strict test typing also passes |
| 18 | PASS: 18 deliberate mutations, all caught |

## API and behavior

The eight exports remain `expand`, `escape`, `list_vars`, `ExpansionError`,
`TemplateSyntaxError`, `UnsetVariableError`, `ParameterError` and `UnsafeTemplateError`.
Signatures and defaults are retained. The expansion options are keyword-only.
`__version__` and the distribution version are 1.0.0; `py.typed` is included.
All 15 doctest examples pass; every public function and exception has executable examples. No documentation imports
the public API from private modules. Source files are at most 200 lines.

Intentional changes from the installed PyPI 0.2.1, all listed in CHANGELOG and GUIDE:

- Required-parameter messages no longer print the expanded word. `detail`, `name` and
  `position` retain their values. Variable names over 80 characters are omitted from
  messages, but retained in `name`.
- Invalid command-line arguments and `--set` values are not echoed in diagnostics.
- `max_output` rejects booleans and non-integers with `TypeError`, and negatives with
  `ValueError`, including empty input.
- Malformed bracket patterns are scanned linearly. Pattern work accounting includes
  bracket contents and is checked before compilation.

Caller-supplied mapping exceptions propagate. Explicit exception construction remains
the caller's responsibility. Diagnostic words are sensitive when read through `detail`;
variable identifiers and filesystem paths must not be used to carry credentials.

## Ground truth

Fetched during this run:

- [PyPI JSON](https://pypi.org/pypi/shtemplate/json): latest release 0.2.1.
- [POSIX.1-2024 Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html):
  357,953 bytes; SHA-256
  `0889867a53fe12508a71e8739ec23ecdddc95e6f67697c98e26acc8ff0ec1acd`.
  The current fetch matches the existing manifest. Specification tests verify that
  the cited input/output pairs really occur in the page.

`tests/upstream/MANIFEST.json` records URL, edition, date, size, hash and license.
`scripts/fetch_upstream.py` reproduces the fetch; `SHTEMPLATE_UPSTREAM` selects an
external directory. Fetched specification text is not committed or distributed.
Those tests skip cleanly without the download and reject a changed hash.

The existing corpus consists of generated templates and actual shell outputs, rather
than copied third-party test data. Its generation rules and seed are in
`scripts/build_corpus.py`. This run reproduced every recorded Bash result using the
local Git Bash 5.3.9 executable (all 1,644 cases). Another 400 seeded combinations of all defaulting operators,
strict mode and assignment visibility agreed with real Bash. WSL/dash is unavailable;
the historical dash outputs remain checked with their documented deviations.
`SHTEMPLATE_BASH` enables both live Bash tests. No template from an untrusted source
is sent to the shell reference.

## Contract and robustness evidence

The suite pins all documented operator forms in set, empty and unset states, lazy words,
assignment isolation, quoting, Unicode lengths, pattern direction and greediness,
typed errors, positions, diagnostic privacy, output limits, API exports, version and
type marker. CLI checks cover stdin, files, output bytes, environment precedence,
UTF-8 failures, listing, strict/safe modes, errors and module execution.

Fuzzing uses eight fixed seeds with 2,500 templates each and three further seeds with
500 escaping round trips each. Process-start functions are replaced with failures
while untrusted templates are expanded. Large plain text, nested input, exponential
assignments and pattern-work limits have dedicated contracts. Unclosed bracket patterns
are exercised at 1,000, 4,000 and 16,000 repetitions, with and without an inner class
terminator. Another 80,000 seeded pattern-removal comparisons against the actual PyPI
0.2.1 wheel agree exactly (seed 20261103). The timeout is 300 seconds per test.

## Packaging and upgrade

`python -m build` produced the sdist and built its wheel. Both passed
`python -m twine check --strict`. The wheel has 17 members: package modules, `py.typed`,
metadata, the console entry point and LICENSE. The sdist has 43 members: source,
tests and their generated corpus, manifest, development scripts, docs, LICENSE and
metadata. Neither includes a fetched specification, caches, scratch files or reports.
There are no runtime dependencies. Metadata is Production/Stable with Python 3.10
through 3.14, MIT, keywords and Homepage/Source/Issues/Changelog URLs.

`scripts/e2e_wheel.py` builds the distributions, creates a new venv, installs actual
PyPI 0.2.1 and runs `scripts/upgrade_probe.py` outside the repository. It upgrades that
installation to the local wheel and verifies stable behavior and documented changes.
The installed command is driven by subprocess for files, stdin, flags and failures;
the import path is checked to be in the venv.

## Interpreter matrix

All 12 available CPython versions/builds passed. Launcher entries pointing to deleted
installations are excluded; no discovered supported version remains untested.
Duplicate installations of the same CPython version/build are represented once.
The suite is extracted from the sdist without `src`, so it imports the installed wheel.
Embedded runtimes are copied before their paths are configured; original installations
are not modified. Every tested runtime also executes `python -m shtemplate` externally.


| CPython | Installed-wheel suite | Module CLI |
| --- | --- | --- |
| 3.13.2 | 296 passed, 4 skipped | PASS |
| 3.12.10 | 296 passed, 4 skipped | PASS |
| 3.11.9 | 296 passed, 4 skipped | PASS |
| 3.10.11 | 296 passed, 4 skipped | PASS |
| 3.14.10t | 296 passed, 4 skipped | PASS |
| 3.13.18 | 296 passed, 4 skipped | PASS |
| 3.14.10 | 296 passed, 4 skipped | PASS |
| 3.12.16 | 296 passed, 4 skipped | PASS |
| 3.11.18 | 296 passed, 4 skipped | PASS |
| 3.10.22 | 296 passed, 4 skipped | PASS |
| 3.14.6 | 296 passed, 4 skipped | PASS |
| 3.11.11 | 296 passed, 4 skipped | PASS |

The four skips are the separately executed wheel e2e and two live Bash tests, plus
unavailable WSL/dash. No 3.13 free-threaded runtime is installed here.

## Mutation round

All 18 deliberate bugs were killed on the final source, one per scratch copy.
The release source was never modified. The work-limit mutant first hit the 300-second
fuzz timeout; its focused bracket-budget contract also fails immediately.

| # | Mutation | Contract that failed |
| --- | --- | --- |
| 1 | Ignore empty values in colon operators | `test_documented_forms` (`:-`) |
| 2 | Reverse alternate-word selection | `test_documented_forms` (`:+`) |
| 3 | Drop assignment export | `test_assigned_collects_the_assignments` |
| 4 | Ignore assignment overlay on lookup | `test_readme_example` (assignment visibility) |
| 5 | Add one to parameter length | `test_documented_forms` (length) |
| 6 | Disable strict mode | `test_errors_go_to_stderr_with_status_1` |
| 7 | Disable unsafe-construct rejection | `test_errors_go_to_stderr_with_status_1` |
| 8 | Reject output exactly at its limit | `test_max_output_applies_without_safe_mode` |
| 9 | Wrong negative-limit error class | `test_output_limit_rejects_negative_numbers_even_for_empty_input` |
| 10 | Print the sensitive required word | `test_errors_go_to_stderr_with_status_1` |
| 11 | Omit a name at 80 rather than 81 characters | `test_error_name_display_boundary` |
| 12 | Swap shortest and longest prefix removal | `test_readme_example` (pattern removals) |
| 13 | Leave one extra suffix character | `test_documented_forms` (suffix removal) |
| 14 | Disable pattern-work limit | `test_pattern_work_budget_counts_bracket_members` |
| 15 | Reverse variable-list order | `test_list_vars` |
| 16 | Do not escape dollar signs | `test_list_vars_and_escape_promises` |
| 17 | Reject nesting at 64 rather than 65 | `test_nesting_depth_is_bounded` |
| 18 | Return success for CLI errors | `test_errors_go_to_stderr_with_status_1` |

## Gates

`ruff format --check .`, `ruff check .`, `mypy --strict src` and
`mypy --strict src tests` pass, each command run on its own. With the fetched POSIX
page, `SHTEMPLATE_BASH` and `SHTEMPLATE_E2E=1`, the final suite is **299 passed,
1 skipped** in 222.79 seconds. The only skip is WSL/dash, unavailable on this machine.
The wheel upgrade, live Bash corpus and fresh seeded Bash comparisons all passed.

## QA round 1 fixes

Reviewed base: `ff22ae389f0a9758b6d9587dea0cadd34d1be91f`, branch `release/1.0.0`.
Fix date: 2026-11-03. All 20 reported findings are addressed; none is disputed.
Fix commit: `3d57ebb58de837575388e1cfb5c5fff0ba4afaaf`
(`fix certification QA findings`).
Independent lens re-verification remains pending; this section records fix evidence,
not a replacement verdict for any lens.

| Finding | Change and regression evidence |
| --- | --- |
| A-001 | GUIDE, README and expand docstring describe nested parameter evaluation, assignment and errors inside command-like text; three nested-evaluation contracts |
| A-002 | GUIDE and error module describe optional positions and identify both resource-limit errors; unknown-position contracts |
| A-003 | escape docstring and GUIDE explicitly exclude NUL from the shell comparison; Python NUL round-trip contract and live Bash check |
| A-004 | GUIDE qualifies the backslash example by verified Bash 5.3.9 context; live stdin comparison |
| B-01 | Parse collating symbols as lower and upper range endpoints; mixed endpoints, boundary characters and all four removals |
| B-02 | Assignment returns the value after quote removal; both assignment operators, three quoting forms and enclosing quotes |
| B-03 | Double-quoted patterns preserve backslash before a brace; direct and nested prefix/suffix patterns |
| C-01 | Single-character parser branches precede tail searches; 8,000/16,000/32,000 apostrophe runs through expand and list_vars |
| C-02 | Check cumulative output before the next sibling; observed mapping reads, transactional sink and bounded traced allocation |
| C-03 | Normalize string and integer subclasses using base implementations; hostile lengths, comparisons and conversions |
| C-04 | Normalize text before parser caching; unhashable subclasses accepted by expand and list_vars |
| C-05 | Validate text, mapping, sink, boolean options and fetched values; consistent TypeError without input contents, lazy unused values |
| C-06 | Bound filesystem diagnostics and source labels; subprocess tests for 12,000-character input, env-file and output paths |
| E-01 | Accept exactly 1,000,000 safe-output characters and reject 1,000,001; M13 killed |
| E-02 | Accept the exact ten-times work budget and reject the next value length; M17 killed |
| E-03 | Default error positions and output/work-limit positions remain None; M27 killed |
| E-04 | Repeated --set uses the last value in a subprocess; M35 killed |
| E-05 | --list-vars -o writes exact file bytes with empty stdout; M39 killed |
| E-06 | --set overrides both env-file and process values; M44 killed by both subprocess tests |
| E-07 | Omitted/None environments ignore a seeded process variable; explicit os.environ reads it; M10 killed |

The new behavior contracts ran before production changes: **60 failed, 8 passed**.
The apostrophe contract took 20.01 seconds and the sibling-assignment case peaked at
128,013,122 traced bytes on the original code. After the fixes, all initial 68 cases
passed, including the five-second parsing bound and five-million-byte allocation bound.
The final resource probe took 0.196 seconds for both parser entry points on 64,000
apostrophes and measured 2,072,837 peak bytes for the 128-sibling assignment case.
Four further contracts cover the clarified command-like text and NUL documentation.
Every changed behavior is recorded in CHANGELOG; public names and signatures remain stable.

Fresh local Git for Windows Bash 5.3.9 comparisons passed for all 101 handwritten
range, assignment, brace and escaped-backslash cases. Bash also confirmed that NUL
does not survive the shell here-document comparison. The shell scripts used stdin
and captured pipes without device-file redirection.

All seven reported surviving mutations were replayed in separate scratch source copies.
Each produced an assertion failure in its new contract (M44 failed both source-precedence
contracts); no timeout or collection failure is counted as a kill.

Evidence is retained under `C:/lianes8-build/codex-pylib/scratch/shtemplate-cert/fix-r1/`:
`red.log`, `bash-results.json`, `mutation-results.json`, and per-mutant `result.log` files.
All pytest runs use a 300-second per-test timeout and a scratch basetemp. The POSIX
chapter was fetched again into scratch and matched the repository manifest.

Final round gates: `ruff format --check .`, `ruff check .`, `mypy --strict src`
and `pytest` each exit 0. Strict typing also passes for `src tests` (33 files).
With the fetched POSIX page and `SHTEMPLATE_E2E=1`, the suite reports **369 passed,
3 skipped** in 29.71 seconds. The installed-wheel build, clean installation, CLI and
upgrade from PyPI 0.2.1 pass. The skips are the two optional historical live Bash
tests and unavailable WSL/dash; the separate 101-case Bash check above covers the
changed shell semantics without the legacy helper's device-file redirection.
The full suite log is `full.log`; the resource probe is `resources.json`.

## QA round 2 fixes

Reviewed base: `12939f923c32fbc6ac558b229f98515ec4a28c9c`, branch `release/1.0.0`.
Fix date: 2026-11-03. All four reported findings are addressed; none is disputed.
Fix commit: `27c66b20bf09e54ea0a7618bd97dbcbf3bce16a7`
(`pin assignment sink and diagnostic path contracts`).

These findings identify missing contracts. The existing implementation already has
the required behavior, so production code, public API and runtime behavior are unchanged.
The new contracts pass on the reviewed base and fail under each reported mutation.
CHANGELOG records the added coverage. Independent lens re-verification remains pending.

| Finding | Added contract and mutation evidence |
| --- | --- |
| E-08 | `test_read_only_assignment_sink_raises_type_error` rejects MappingProxyType for empty and assigning templates; N04 produces two AttributeError failures. `test_assignment_sink_accepts_mutable_mapping` verifies UserDict with both templates and preserves existing entries. |
| E-09 | `test_filesystem_diagnostic_path_boundary` checks nonexistent paths of exactly 200 and 201 characters for template, env-file and output arguments; N22 fails all three 201-character cases while the three 200-character cases pass. |
| E-10 | `test_invalid_utf8_omits_long_existing_path` reads byte 0xff from regular files at 220-character paths through template and env-file arguments; N23 fails both cases. Exit 1, empty stdout, omitted path and byte offset are pinned. |
| E-11 | `test_malformed_dotenv_omits_long_existing_path` reads malformed dotenv content from a regular file at a 220-character path; N24 fails. Exit 1, empty stdout, omitted path, line 2 and the useful syntax diagnostic are pinned. |

Twelve new cases pass. The two affected test modules report **47 passed** on unchanged
production code. All four mutations were replayed separately in scratch source copies;
each failed its new behavior contract, without collection failures or timeouts.
Evidence is under `C:/lianes8-build/codex-pylib/scratch/shtemplate-cert/fix-r2/`:
`replay.py`, `baseline.log`, `mutation-results.json`, and `N04.log`, `N22.log`,
`N23.log`, `N24.log`.

`ruff format --check .`, `ruff check .`, `mypy --strict src` and `pytest` each exit 0.
Strict typing also passes for `src tests` (33 files). With the freshly fetched,
manifest-verified POSIX page and `SHTEMPLATE_E2E=1`, the full suite reports
**381 passed, 3 skipped** in 36.13 seconds, including the installed-wheel build,
CLI and upgrade from PyPI 0.2.1. The skips are the two optional live Bash tests and
unavailable WSL/dash. All pytest runs use a 300-second per-test timeout and scratch
basetemp; temporary files remain under scratch. The full suite log is `full.log`.

## Remaining certification stages

Items 16 and 19 remain incomplete. QA round 1 reported findings for lenses a, b, c
and e; their fixes await independent re-verification. The independent review, final
lens verdicts, merge and publication are separate stages and are not marked passed.
