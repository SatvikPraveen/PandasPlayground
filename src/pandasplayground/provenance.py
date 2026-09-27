"""Run manifests: record exactly what went into, and came out of, a computation.

A manifest captures input/output file hashes, row counts, parameters, library versions,
platform and the git commit, so that any exported artefact can be traced and re-derived.
"""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from pandasplayground.io import frame_fingerprint, sha256_file

TRACKED_PACKAGES = ("pandas", "numpy", "scipy", "pyarrow", "openpyxl", "pandasplayground")


def package_versions(packages: tuple[str, ...] = TRACKED_PACKAGES) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def environment_info() -> dict[str, Any]:
    """Interpreter, OS and hardware details relevant to reproducing a result or a timing."""
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "cpu_count": _cpu_count(),
        "packages": package_versions(),
    }


def _cpu_count() -> int | None:
    import os

    return os.cpu_count()


def git_state(cwd: Path | None = None) -> dict[str, Any]:
    """Current commit SHA and whether the working tree has uncommitted changes (``None`` outside git)."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True, check=True
            ).stdout.strip()
        )
        return {"commit": sha, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


@dataclass
class ArtifactRecord:
    path: str
    sha256: str
    rows: int | None = None
    columns: int | None = None
    fingerprint: str | None = None


def describe_file(path: Path, frame: pd.DataFrame | None = None, root: Path | None = None) -> ArtifactRecord:
    shown = (
        path.resolve().relative_to(root.resolve()) if root and path.resolve().is_relative_to(root.resolve()) else path
    )
    return ArtifactRecord(
        path=str(shown),
        sha256=sha256_file(path),
        rows=None if frame is None else len(frame),
        columns=None if frame is None else frame.shape[1],
        fingerprint=None if frame is None else frame_fingerprint(frame),
    )


@dataclass
class RunManifest:
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    inputs: list[ArtifactRecord] = field(default_factory=list)
    outputs: list[ArtifactRecord] = field(default_factory=list)
    validation: dict[str, bool] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    finished_at: str | None = None
    environment: dict[str, Any] = field(default_factory=environment_info)
    git: dict[str, Any] = field(default_factory=git_state)

    def finish(self) -> RunManifest:
        self.finished_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str) + "\n")
        return path
