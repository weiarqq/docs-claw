from __future__ import annotations

import re
from pathlib import Path


_SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in (current, *current.parents):
        if (path / ".git").exists() or (path / "pyproject.toml").exists():
            return path
    return current


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_id(value: str) -> str:
    if not _SAFE_ID_RE.match(value):
        raise ValueError(
            "source id must use lowercase letters, numbers, underscores, or hyphens"
        )
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError("source id cannot contain path traversal")
    return value
