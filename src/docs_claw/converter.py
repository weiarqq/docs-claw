from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from markdownify import markdownify as html_to_markdown

from docs_claw.adapters.sphinx import extract_main_content
from docs_claw.paths import ensure_dir
from docs_claw.registry import SourceConfig


@dataclass(frozen=True)
class ConvertResult:
    pages_converted: int
    pages_skipped: int


def _frontmatter(page: dict[str, str | int], source: SourceConfig) -> str:
    lines = [
        "---",
        f"source_id: {source.id}",
        f"source_url: {page['url']}",
        f"title: {str(page['title']).replace(':', ' -')}",
        f"fetched_at: \"{page['fetched_at']}\"",
        f"content_hash: {page['content_hash']}",
        f"site_type: {source.type}",
        "---",
        "",
    ]
    return "\n".join(lines)


def convert_source(root: Path, source: SourceConfig) -> ConvertResult:
    manifest_path = root / "raw" / source.id / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = ensure_dir(root / "docs" / source.id / "pages")
    converted = 0
    skipped = 0

    for page in manifest.get("pages", []):
        raw_path = root / str(page["raw_path"])
        html = raw_path.read_text(encoding="utf-8")
        main_html = extract_main_content(html)
        markdown = html_to_markdown(main_html, heading_style="ATX").strip()
        if not markdown:
            skipped += 1
            continue
        output_path = output_dir / f"{raw_path.stem}.md"
        output_path.write_text(_frontmatter(page, source) + markdown + "\n", encoding="utf-8")
        converted += 1

    return ConvertResult(pages_converted=converted, pages_skipped=skipped)
