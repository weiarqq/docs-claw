from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from docs_claw.paths import ensure_dir
from docs_claw.registry import SourceConfig


@dataclass(frozen=True)
class WikiResult:
    pages_indexed: int
    topics_written: int


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "untitled"


def _parse_page(path: Path) -> dict[str, str | Path | list[str]]:
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = text
    if text.startswith("---\n"):
        _start, frontmatter, body = text.split("---\n", 2)
        for line in frontmatter.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')
    headings = [line.lstrip("# ").strip() for line in body.splitlines() if line.startswith("## ")]
    return {
        "path": path,
        "title": meta.get("title", path.stem),
        "source_url": meta.get("source_url", ""),
        "headings": headings,
    }


def build_wiki(root: Path, source: SourceConfig) -> WikiResult:
    pages_dir = root / "docs" / source.id / "pages"
    if not pages_dir.exists():
        raise FileNotFoundError(f"converted docs not found: {pages_dir}")
    wiki_dir = ensure_dir(root / "wiki" / source.id)
    topics_dir = ensure_dir(wiki_dir / "topics")
    pages = [_parse_page(path) for path in sorted(pages_dir.glob("*.md"))]

    index_lines = [f"# {source.id} Documentation Index", ""]
    for page in pages:
        rel = Path(page["path"]).relative_to(root)
        index_lines.append(f"- [{page['title']}](../../{rel}) - {page['source_url']}")
    (wiki_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    overview = [
        f"# {source.id} Documentation Overview",
        "",
        f"Source URL: {source.url}",
        f"Site type: {source.type}",
        f"Page count: {len(pages)}",
        f"Generated at: {_now()}",
    ]
    (wiki_dir / "overview.md").write_text("\n".join(overview) + "\n", encoding="utf-8")

    topics: dict[str, list[dict[str, str | Path | list[str]]]] = {}
    for page in pages:
        for heading in page["headings"]:
            topics.setdefault(str(heading), []).append(page)
    for topic_path in topics_dir.glob("*.md"):
        topic_path.unlink()
    for topic, topic_pages in sorted(topics.items()):
        lines = [f"# {topic}", "", f"Source: {source.id}", "", "## Related Pages", ""]
        for page in topic_pages:
            rel = Path(page["path"]).relative_to(root)
            lines.append(f"- [{page['title']}](../../../{rel}) - {page['source_url']}")
        (topics_dir / f"{_slug(topic)}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    log_path = wiki_dir / "log.md"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"## [{_now()}] build-wiki | {source.id} | pages={len(pages)} topics={len(topics)}\n")
    return WikiResult(pages_indexed=len(pages), topics_written=len(topics))
