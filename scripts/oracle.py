"""Expand templates with a real POSIX shell (dash or bash --posix) through WSL.

Each template is placed in an unquoted here-document, which applies parameter
expansion, backslash escapes and quote handling exactly as a template expects.
Every case runs in its own subshell, so assignments and ``:?`` exits stay local.

Usage as a library::

    from oracle import run_shell
    results = run_shell("dash", [("${X:-d}", {"X": ""}, False)])

Each result is ``("ok", output)`` or ``("error", "")``.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping, Sequence

Case = tuple[str, Mapping[str, str], bool]
Result = tuple[str, str]

_SHELLS = {"dash": ["dash", "-s"], "bash": ["bash", "--posix", "-s"]}
_MARK = "__SHT_ORACLE_CASE__"


def wsl_available() -> bool:
    """Return True when ``wsl`` can run ``dash``."""
    if shutil.which("wsl") is None:
        return False
    try:
        done = subprocess.run(
            ["wsl", "-e", "dash", "-c", "printf ok"],
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.stdout == b"ok"


def _quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def build_script(cases: Sequence[Case]) -> str:
    """Return one shell script that expands every case in its own subshell."""
    lines = ["unset IFS"]
    for index, (template, env, strict) in enumerate(cases):
        delimiter = f"__SHT_END_{index}__"
        if delimiter in template:
            raise ValueError("template contains the here-document delimiter")
        assigns = "".join(f"{name}={_quote(value)}; " for name, value in env.items())
        flag = "set -u; " if strict else ""
        lines.append(f"printf '%s\\n' '{_MARK}{index}'")
        body = _quote(f"cat <<{delimiter}\n{template}\n{delimiter}\n")
        # eval keeps a syntax error inside one template from aborting the whole script.
        lines.append(f"( {flag}{assigns}eval {body} ) 2>/dev/null")
        lines.append(f"printf '\\n%s%s\\n' '{_MARK}rc=' \"$?\"")
    return "\n".join(lines) + "\n"


def parse_output(raw: str, count: int) -> list[Result]:
    """Split the combined shell output back into one result per case."""
    results: list[Result] = []
    for index in range(count):
        head = f"{_MARK}{index}\n"
        start = raw.index(head) + len(head)
        end = raw.index(f"\n{_MARK}rc=", start)
        body = raw[start:end]
        rc_line = raw[end + 1 :].split("\n", 1)[0]
        status = rc_line[len(_MARK) + 3 :]
        if status != "0":
            results.append(("error", ""))
        else:
            # cat echoes the here-document, which always ends with one newline.
            results.append(("ok", body[:-1] if body.endswith("\n") else body))
    return results


def run_shell(shell: str, cases: Sequence[Case], timeout: float = 300) -> list[Result]:
    """Run every case through ``shell`` ("dash" or "bash") inside WSL."""
    script = build_script(cases)
    done = subprocess.run(
        ["wsl", "-e", "env", "-i", "LC_ALL=C.UTF-8", "PATH=/usr/bin:/bin", *_SHELLS[shell]],
        input=script.encode("utf-8"),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return parse_output(done.stdout.decode("utf-8", errors="surrogateescape"), len(cases))
