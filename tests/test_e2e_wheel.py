"""Opt-in end-to-end check of the built wheel (set SHTEMPLATE_E2E=1 to run).

It builds the wheel, installs it into a throwaway virtual environment and drives
the installed ``shtemplate`` command through ``scripts/e2e_wheel.py``. It needs
network access for the build backend, so it does not run by default.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "e2e_wheel.py"


@pytest.mark.skipif(os.environ.get("SHTEMPLATE_E2E") != "1", reason="set SHTEMPLATE_E2E=1")
def test_installed_wheel_end_to_end() -> None:
    done = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "e2e: all checks passed" in done.stdout
