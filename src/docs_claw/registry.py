from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml

from docs_claw.paths import ensure_dir, safe_id


@dataclass(frozen=True)
class SourceConfig:
    id: str
    url: str
    type: str
    allowed_domains: list[str]
    allowed_path_prefixes: list[str]
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_path_prefix(url: str) -> str:
    path = urlparse(url).path or "/"
    if path.endswith("/"):
        return path
    parent = path.rsplit("/", 1)[0]
    return f"{parent}/" if parent else "/"


def _source_path(root: Path, source_id: str) -> Path:
    return root / "sources" / safe_id(source_id) / "source.yml"


def add_source(
    root: Path,
    source_id: str,
    url: str,
    site_type: str = "sphinx",
) -> SourceConfig:
    safe = safe_id(source_id)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be an absolute http(s) URL")
    if site_type != "sphinx":
        raise ValueError("only sphinx sources are supported")

    now = _now()
    existing = _source_path(root, safe)
    created_at = now
    if existing.exists():
        created_at = load_source(root, safe).created_at

    source = SourceConfig(
        id=safe,
        url=url,
        type=site_type,
        allowed_domains=[parsed.netloc],
        allowed_path_prefixes=[_default_path_prefix(url)],
        created_at=created_at,
        updated_at=now,
    )
    path = _source_path(root, safe)
    ensure_dir(path.parent)
    path.write_text(yaml.safe_dump(asdict(source), sort_keys=False), encoding="utf-8")
    return source


def load_source(root: Path, source_id: str) -> SourceConfig:
    path = _source_path(root, source_id)
    if not path.exists():
        raise FileNotFoundError(f"source not found: {source_id}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SourceConfig(**data)


def list_sources(root: Path) -> list[SourceConfig]:
    sources_dir = root / "sources"
    if not sources_dir.exists():
        return []
    result = []
    for path in sorted(sources_dir.glob("*/source.yml")):
        result.append(load_source(root, path.parent.name))
    return result
