"""Build the wheel, install it in a throwaway venv and drive the installed command.

Run from the repository root: ``python scripts/e2e_wheel.py``. Exits 0 when every
check passes. Needs network access for the build backend and the ``build`` package.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(
    cmd: list[str], *, stdin: str = "", env: dict[str, str] | None = None, cwd: Path
) -> tuple[int, str, str]:
    done = subprocess.run(
        cmd, input=stdin.encode("utf-8"), capture_output=True, env=env, cwd=cwd, check=False
    )
    return done.returncode, done.stdout.decode("utf-8"), done.stderr.decode("utf-8")


def check(label: str, condition: bool, detail: object = "") -> None:
    print(("ok   " if condition else "FAIL ") + label + (f": {detail!r}" if not condition else ""))
    if not condition:
        raise SystemExit(1)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="shtemplate-e2e-") as raw:
        work = Path(raw)
        code, out, err = run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(work / "dist"), str(ROOT)],
            cwd=work,
        )
        check("wheel builds", code == 0, err[-2000:])
        wheel = next((work / "dist").glob("shtemplate-*.whl"))
        names = zipfile.ZipFile(wheel).namelist()
        check("wheel ships py.typed", "shtemplate/py.typed" in names, names)
        check(
            "wheel has no tests or scripts",
            not any(n.startswith(("tests/", "scripts/")) for n in names),
        )
        entry = [n for n in names if n.endswith("entry_points.txt")]
        text = zipfile.ZipFile(wheel).read(entry[0]).decode() if entry else ""
        check("console script declared", "shtemplate = shtemplate._cli:main" in text, text)

        venv = work / "venv"
        check("venv created", run([sys.executable, "-m", "venv", str(venv)], cwd=work)[0] == 0)
        bindir = venv / ("Scripts" if os.name == "nt" else "bin")
        python = str(bindir / "python")
        code, _, err = run(
            [python, "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)], cwd=work
        )
        check("wheel installs", code == 0, err[-2000:])
        tool = str(bindir / "shtemplate")
        base = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}

        code, out, _ = run([tool, "--version"], cwd=work, env=base)
        check("--version", code == 0 and out.strip().startswith("shtemplate 0.2"), out)
        code, out, _ = run([tool, "--help"], cwd=work, env=base)
        check("--help shows examples", code == 0 and "examples:" in out, out)
        env = {**base, "SHT_USER": "ada"}
        code, out, _ = run(
            [tool], stdin="Hi ${SHT_USER:-x} ${SHT_NONE:-guest}\n", cwd=work, env=env
        )
        check("stdin against the environment", (code, out) == (0, "Hi ada guest\n"), out)
        (work / "a.env").write_text("FILE=report.tar.gz\nexport HOST='db.local'\n", "utf-8")
        (work / "t.tpl").write_text("${FILE%%.*}@${HOST} ${#FILE}", "utf-8")
        code, out, _ = run([tool, "-i", "-e", "a.env", "t.tpl"], cwd=work, env=base)
        check("env file and patterns", (code, out) == (0, "report@db.local 13"), out)
        code, out, _ = run([tool, "-i", "-s", "X=1", "-o", "out.txt", "t.tpl"], cwd=work, env=base)
        check("-o writes a file", code == 0 and (work / "out.txt").read_text("utf-8") == "@ 0")
        code, out, _ = run([tool, "--list-vars", "t.tpl"], cwd=work, env=base)
        check("--list-vars", (code, out.split()) == (0, ["FILE", "HOST"]), out)
        code, out, err = run([tool, "-i", "--strict"], stdin="$NOPE", cwd=work, env=base)
        check("--strict fails with exit 1", (code, out) == (1, "") and "NOPE" in err, err)
        code, out, err = run([tool, "--safe"], stdin="$(touch pwned)", cwd=work, env=base)
        check("--safe rejects command substitution", code == 1 and "not allowed" in err, err)
        code, out, _ = run([tool, "-i"], stdin="`touch pwned` $(touch pwned)", cwd=work, env=base)
        check("nothing is executed", code == 0 and not (work / "pwned").exists(), out)
        code, out, _ = run(
            [python, "-m", "shtemplate", "-i", "-s", "A=1"], stdin="$A", cwd=work, env=base
        )
        check("python -m shtemplate", (code, out) == (0, "1"), out)
        probe = (
            "import shtemplate; print(shtemplate.__file__); print(shtemplate.expand('${A:-ok}'))"
        )
        code, out, _ = run([python, "-c", probe], cwd=work, env=base)
        check(
            "library imports from the venv",
            code == 0 and "venv" in out and out.splitlines()[-1:] == ["ok"],
            out,
        )
    print("e2e: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
