from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from docs_claw.adapters.sphinx import extract_links, extract_title
from docs_claw.paths import ensure_dir
from docs_claw.registry import SourceConfig


Fetcher = Callable[[str], str]


@dataclass(frozen=True)
class FetchError(Exception):
    url: str
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        status = f"HTTP {self.status_code}: " if self.status_code is not None else ""
        return f"{status}{self.message}"


@dataclass(frozen=True)
class CrawlResult:
    pages_crawled: int
    manifest_path: Path
    pages_failed: int = 0


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_fetcher(
    ignore_proxy: bool = False,
    request: Callable[..., Any] | None = None,
) -> Fetcher:
    def fetch(url: str) -> str:
        try:
            if request is not None:
                response = request(url, trust_env=not ignore_proxy)
            else:
                with httpx.Client(
                    follow_redirects=True,
                    timeout=30,
                    trust_env=not ignore_proxy,
                ) as client:
                    response = client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as error:
            raise FetchError(
                url=url,
                status_code=error.response.status_code,
                message=str(error),
            ) from error
        except httpx.HTTPError as error:
            raise FetchError(url=url, message=str(error)) from error

    return fetch


def _raw_filename(url: str) -> str:
    return f"{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}.html"


def crawl_source(
    root: Path,
    source: SourceConfig,
    fetcher: Fetcher | None = None,
    max_pages: int = 500,
    ignore_proxy: bool = False,
) -> CrawlResult:
    if source.type != "sphinx":
        raise ValueError(f"unsupported source type: {source.type}")

    fetch = fetcher or make_fetcher(ignore_proxy=ignore_proxy)
    raw_dir = ensure_dir(root / "raw" / source.id / "pages")
    manifest_path = root / "raw" / source.id / "manifest.json"
    queue: list[tuple[str, str | None]] = [(source.url, None)]
    seen: set[str] = set()
    pages: list[dict[str, str | int]] = []
    errors: list[dict[str, str | int | None]] = []

    while queue and len(seen) < max_pages:
        url, referrer = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            html = fetch(url)
        except FetchError as error:
            errors.append(
                {
                    "url": error.url,
                    "referrer": referrer,
                    "status": error.status_code,
                    "error": error.message,
                }
            )
            continue
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
            queued_urls = {queued_url for queued_url, _queued_referrer in queue}
            if link not in seen and link not in queued_urls:
                queue.append((link, url))

    manifest = {
        "source_id": source.id,
        "source_url": source.url,
        "pages": pages,
        "errors": errors,
    }
    ensure_dir(manifest_path.parent)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return CrawlResult(
        pages_crawled=len(pages),
        manifest_path=manifest_path,
        pages_failed=len(errors),
    )
