from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TESTS_DIR = ROOT / "tests"
SRC_DIR = ROOT / "src"

cmd = [
    sys.executable,
    "-m",
    "unittest",
    "discover",
    "-s",
    str(TESTS_DIR),
    "-v",
]

env = dict(__import__("os").environ)
env["PYTHONPATH"] = str(SRC_DIR)

result = subprocess.run(cmd, cwd=ROOT, env=env)
raise SystemExit(result.returncode)
