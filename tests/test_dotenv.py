"""The .env reader behind ``shtemplate --env-file``."""

from __future__ import annotations

import pytest

from shtemplate._dotenv import EnvFileError, parse_env


def test_parses_bare_quoted_and_exported_values() -> None:
    text = (
        "# comment\n"
        "\n"
        "A=1\n"
        "export B = two words  \n"
        "C='single $NOT expanded # kept'\n"
        'D="tab\\tnew\\nquote\\" dollar\\$ back\\\\ other\\q"\n'
        "E=\n"
        "F=x # trailing comment\n"
        "G=x#not-a-comment\n"
        "H='q' # comment after quote\n"
        "I=a\t# tab comment\n"
    )
    assert parse_env(text) == {
        "A": "1",
        "B": "two words",
        "C": "single $NOT expanded # kept",
        "D": 'tab\tnew\nquote" dollar$ back\\ other\\q',
        "E": "",
        "F": "x",
        "G": "x#not-a-comment",
        "H": "q",
        "I": "a",
    }


def test_later_duplicates_win() -> None:
    assert parse_env("A=1\nA=2\n") == {"A": "2"}


def test_crlf_lines() -> None:
    assert parse_env("A=1\r\nB=2\r\n") == {"A": "1", "B": "2"}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("novalue", "expected NAME=VALUE"),
        ("1A=x", "expected NAME=VALUE"),
        ("A-B=x", "expected NAME=VALUE"),
        ("=x", "expected NAME=VALUE"),
        ("A='open", "unterminated single quote"),
        ('A="open', "unterminated double quote"),
        ("A='x' junk", "unexpected text"),
    ],
)
def test_errors_name_the_source_and_line(text: str, message: str) -> None:
    with pytest.raises(EnvFileError, match=f"prod.env:2: {message}"):
        parse_env("OK=1\n" + text, "prod.env")
