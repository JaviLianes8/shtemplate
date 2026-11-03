"""Handwritten subprocess contracts for CLI precedence and bounded errors."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(args: list[str], stdin: str = "") -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run(
        [sys.executable, "-m", "shtemplate", *args],
        input=stdin.encode(),
        capture_output=True,
        env=env,
        timeout=30,
    )


def test_repeated_set_uses_last_value() -> None:
    result = run_cli(["-i", "-s", "X=first", "-s", "X=last"], "$X")
    assert (result.returncode, result.stdout, result.stderr) == (0, b"last", b"")


def test_list_vars_honors_output_file(tmp_path: Path) -> None:
    target = tmp_path / "vars.txt"
    result = run_cli(["--list-vars", "-o", str(target)], "$B ${A:-$B}")
    assert (result.returncode, result.stdout, result.stderr) == (0, b"", b"")
    assert target.read_bytes() == b"B\nA\n"


def test_set_overrides_environment_file(tmp_path: Path) -> None:
    source = tmp_path / "input.env"
    source.write_text("X=first\n", encoding="utf-8")
    result = run_cli(["-i", "-e", str(source), "-s", "X=last"], "$X")
    assert (result.returncode, result.stdout, result.stderr) == (0, b"last", b"")


def test_set_overrides_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X", "first")
    result = run_cli(["-s", "X=last"], "$X")
    assert (result.returncode, result.stdout, result.stderr) == (0, b"last", b"")


@pytest.mark.parametrize("option", [[], ["-e"], ["-o"]])
def test_filesystem_diagnostics_bound_long_paths(option: list[str]) -> None:
    result = run_cli(["-i", *option, "q" * 12000])
    assert (result.returncode, result.stdout) == (1, b"")
    size = len(result.stderr)
    assert size < 1000
    assert b"Traceback" not in result.stderr


def path_with_length(parent: Path, length: int) -> Path:
    leaf_length = length - len(str(parent)) - 1
    assert 0 < leaf_length <= 255
    path = parent / ("p" * leaf_length)
    assert len(str(path)) == length
    return path


@pytest.mark.parametrize("length", [200, 201])
@pytest.mark.parametrize("option", [[], ["-e"], ["-o"]])
def test_filesystem_diagnostic_path_boundary(
    tmp_path: Path, length: int, option: list[str]
) -> None:
    path = path_with_length(tmp_path / "missing", length)
    result = run_cli(["-i", *option, str(path)])
    assert (result.returncode, result.stdout) == (1, b"")
    assert result.stderr.startswith(b"shtemplate: error: ")
    assert b"Traceback" not in result.stderr
    if length == 200:
        assert str(path).encode() in result.stderr
        assert b"<path omitted>" not in result.stderr
    else:
        assert str(path).encode() not in result.stderr
        assert b"<path omitted>: " in result.stderr
    assert len(result.stderr) < 1000


@pytest.mark.parametrize("option", [[], ["-e"]])
def test_invalid_utf8_omits_long_existing_path(tmp_path: Path, option: list[str]) -> None:
    path = path_with_length(tmp_path, 220)
    path.write_bytes(b"X=\xff\n")
    result = run_cli(["-i", *option, str(path)])
    assert (result.returncode, result.stdout) == (1, b"")
    assert str(path).encode() not in result.stderr
    assert result.stderr.strip() == (b"shtemplate: error: <path omitted>: not valid UTF-8 (byte 2)")


def test_malformed_dotenv_omits_long_existing_path(tmp_path: Path) -> None:
    path = path_with_length(tmp_path, 220)
    path.write_bytes(b"OK=1\ninvalid input\n")
    result = run_cli(["-i", "-e", str(path)])
    assert (result.returncode, result.stdout) == (1, b"")
    assert str(path).encode() not in result.stderr
    assert result.stderr.strip() == b"shtemplate: error: <path omitted>:2: expected NAME=VALUE"
