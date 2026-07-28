from __future__ import unicode_literals

import os
import subprocess
from pathlib import Path

from . import __version__


def _repo_root():
    return Path(__file__).resolve().parents[1]


def _git_version():
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=str(_repo_root()),
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return completed.stdout.strip()


def get_build_version():
    version = (
        os.environ.get("POSAWESOME_BUILD_VERSION")
        or os.environ.get("BUILD_VERSION")
        or _git_version()
        or __version__
    )
    return version.strip()
