from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

import httpx

from docs_claw.adapters.sphinx import extract_links, extract_title
from docs_claw.paths import ensure_dir
from docs_claw.registry import SourceConfig


Fetcher = Callable[[str], str]


@dataclass(frozen=True)
class CrawlResult:
    pages_crawled: int
    manifest_path: Path


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _default_fetcher(url: str) -> str:
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    return response.text


def _raw_filename(url: str) -> str:
    return f"{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}.html"


def crawl_source(
    root: Path,
    source: SourceConfig,
    fetcher: Fetcher | None = None,
    max_pages: int = 500,
) -> CrawlResult:
    if source.type != "sphinx":
        raise ValueError(f"unsupported source type: {source.type}")

    fetch = fetcher or _default_fetcher
    raw_dir = ensure_dir(root / "raw" / source.id / "pages")
    manifest_path = root / "raw" / source.id / "manifest.json"
    queue = [source.url]
    seen: set[str] = set()
    pages: list[dict[str, str | int]] = []

    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        html = fetch(url)
        content_hash = _hash_text(html)
        filename = _raw_filename(url)
        raw_path = raw_dir / filename
        raw_path.write_text(html, encoding="utf-8")
        pages.append(
            {
                "url": url,
                "raw_path": str(raw_path.relative_to(root)),
                "title": extract_title(html),
                "content_hash": content_hash,
                "fetched_at": _now(),
                "status": 200,
            }
        )
        for link in extract_links(source, url, html):
            if link not in seen and link not in queue:
                queue.append(link)

    manifest = {"source_id": source.id, "source_url": source.url, "pages": pages}
    ensure_dir(manifest_path.parent)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return CrawlResult(pages_crawled=len(pages), manifest_path=manifest_path)
