from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def read_upstream(name: str) -> bytes:
    """Return a third-party test file, checked against tests/upstream/MANIFEST.json.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body


@pytest.fixture(scope="session")
def posix_lines() -> list[str]:
    """The fetched POSIX shell chapter as text lines: tags stripped, entities decoded."""
    page = read_upstream("V3_chap02.html").decode("utf-8")
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    return [line.strip() for line in text.splitlines() if line.strip()]
