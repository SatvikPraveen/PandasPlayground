"""Project paths and global settings.

Paths are resolved relative to the repository root by default and can be overridden with
environment variables so the package works identically in notebooks, CI, Docker and the CLI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

#: Default random seed used anywhere randomness is involved.
DEFAULT_SEED = 42


def _find_project_root(start: Path) -> Path:
    """Walk upwards from ``start`` until a directory containing ``pyproject.toml`` is found."""
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return Path.cwd()


@dataclass(frozen=True)
class ProjectPaths:
    """Canonical locations of project directories."""

    root: Path
    data: Path
    assets: Path
    exports: Path
    runs: Path

    @classmethod
    def from_env(cls, root: Path | None = None) -> ProjectPaths:
        """Build paths, honouring ``PANDASPLAYGROUND_*`` environment variable overrides."""
        base = Path(os.environ.get("PANDASPLAYGROUND_ROOT", root or _find_project_root(Path(__file__).resolve())))

        def _resolve(env: str, default: str) -> Path:
            value = os.environ.get(env)
            return Path(value) if value else base / default

        return cls(
            root=base,
            data=_resolve("PANDASPLAYGROUND_DATA", "data"),
            assets=_resolve("PANDASPLAYGROUND_ASSETS", "assets"),
            exports=_resolve("PANDASPLAYGROUND_EXPORTS", "exports"),
            runs=_resolve("PANDASPLAYGROUND_RUNS", "runs"),
        )


PATHS = ProjectPaths.from_env()
