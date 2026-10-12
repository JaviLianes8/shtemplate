"""The shtemplate command line tool, driven in-process."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from shtemplate import __version__
from shtemplate._cli import main


class FakeStream(io.TextIOWrapper):
    def __init__(self, data: bytes = b"") -> None:
        super().__init__(io.BytesIO(data), encoding="utf-8", newline="")


def run(monkeypatch: pytest.MonkeyPatch, argv: list[str], stdin: str = "") -> tuple[int, str, str]:
    out, err = FakeStream(), io.StringIO()
    monkeypatch.setattr(sys, "stdin", FakeStream(stdin.encode("utf-8")))
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    try:
        code = main(argv)
    except SystemExit as exc:
        code = int(exc.code or 0)
    out.flush()
    assert isinstance(out.buffer, io.BytesIO)
    return code, out.buffer.getvalue().decode("utf-8"), err.getvalue()


def test_expands_stdin_against_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHT_WHO", "ada")
    assert run(monkeypatch, [], "hi ${SHT_WHO:-x}\n") == (0, "hi ada\n", "")


def test_ignore_environment_and_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHT_WHO", "ada")
    code, out, _ = run(monkeypatch, ["-i", "-s", "B=2", "--set", "C=x=y"], "[$SHT_WHO|$B|$C]")
    assert (code, out) == (0, "[|2|x=y]")


def test_env_files_are_layered_in_order(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    first = tmp_path / "a.env"
    first.write_text("# base\nexport HOST=localhost\nPORT=80 # web\n", "utf-8")
    second = tmp_path / "b.env"
    second.write_text("PORT='8080'\nMSG=\"a\\tb $x\"\n", "utf-8")
    template = tmp_path / "t.tpl"
    template.write_text("${HOST}:${PORT} ${MSG}", "utf-8")
    args = ["-i", "-e", str(first), "--env-file", str(second), str(template)]
    assert run(monkeypatch, args) == (0, "localhost:8080 a\tb $x", "")


def test_output_file_is_written_byte_for_byte(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "out.txt"
    code, out, _ = run(monkeypatch, ["-i", "-s", "X=é", "-o", str(target)], "$X\r\n")
    assert (code, out) == (0, "")
    assert target.read_bytes() == "é\r\n".encode()


def test_list_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    code, out, _ = run(monkeypatch, ["--list-vars"], "$HOME ${APP:-${HOME}} ${#X}")
    assert (code, out) == (0, "HOME\nAPP\nX\n")


@pytest.mark.parametrize(
    ("argv", "stdin", "message"),
    [
        (["-i", "--strict"], "$NOPE", "undefined variable: NOPE"),
        (["-i"], "${NOPE:?is required}", "NOPE: is required"),
        (["-i"], "${A", "unterminated"),
        (["--safe"], "$(id)", "command substitution is not allowed"),
        (["-s", "novalue"], "x", "--set expects NAME=VALUE"),
        (["missing-file.tpl"], "", "missing-file.tpl"),
    ],
)
def test_errors_go_to_stderr_with_status_1(
    monkeypatch: pytest.MonkeyPatch, argv: list[str], stdin: str, message: str
) -> None:
    code, out, err = run(monkeypatch, argv, stdin)
    assert (code, out) == (1, "")
    assert err.startswith("shtemplate: error: ") and message in err


def test_bad_env_file_reports_file_and_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = tmp_path / "bad.env"
    env.write_text("OK=1\nnot a pair\n", "utf-8")
    code, _, err = run(monkeypatch, ["-e", str(env)], "x")
    assert code == 1 and f"{env}:2: expected NAME=VALUE" in err


def test_usage_errors_exit_1(monkeypatch: pytest.MonkeyPatch) -> None:
    code, _, err = run(monkeypatch, ["--no-such-flag"])
    assert code == 1 and "unrecognized arguments" in err


def test_help_has_runnable_examples(monkeypatch: pytest.MonkeyPatch) -> None:
    code, out, _ = run(monkeypatch, ["--help"])
    assert code == 0
    for text in ("examples:", "--list-vars config.tpl", "--strict --safe", "--env-file"):
        assert text in out


def test_version(monkeypatch: pytest.MonkeyPatch) -> None:
    assert run(monkeypatch, ["--version"]) == (0, f"shtemplate {__version__}\n", "")


def test_invalid_utf8_input_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", FakeStream(b"\xff\xfe$X"))
    err = io.StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    assert main(["-i"]) == 1
    assert "shtemplate: error:" in err.getvalue()
