from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchResult:
    path: Path
    title: str
    source_url: str
    score: int
    snippet: str


def _frontmatter_value(text: str, key: str) -> str:
    if not text.startswith("---\n"):
        return ""
    try:
        _start, frontmatter, _body = text.split("---\n", 2)
    except ValueError:
        return ""
    prefix = f"{key}:"
    for line in frontmatter.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _title(text: str, path: Path) -> str:
    value = _frontmatter_value(text, "title")
    if value:
        return value
    for line in text.splitlines():
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    return path.stem


def _source_url(text: str) -> str:
    value = _frontmatter_value(text, "source_url")
    if value:
        return value
    match = re.search(r"https?://\S+", text)
    return match.group(0).rstrip(").,]") if match else ""


def _snippet(text: str, query: str) -> str:
    lower = text.lower()
    index = lower.find(query.lower())
    if index == -1:
        return ""
    start = max(0, index - 80)
    end = min(len(text), index + 160)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def search_source(root: Path, source_id: str, query: str, limit: int = 10) -> list[SearchResult]:
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return []
    candidates = list((root / "docs" / source_id).glob("**/*.md")) + list(
        (root / "wiki" / source_id).glob("**/*.md")
    )
    results: list[SearchResult] = []
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        title = _title(text, path)
        source_url = _source_url(text)
        heading_text = "\n".join(line for line in text.splitlines() if line.startswith("#"))
        score = 0
        for term in terms:
            score += title.lower().count(term) * 10
            score += heading_text.lower().count(term) * 5
            score += source_url.lower().count(term) * 3
            score += text.lower().count(term)
        if score:
            results.append(SearchResult(path, title, source_url, score, _snippet(text, query)))
    return sorted(results, key=lambda result: (-result.score, str(result.path)))[:limit]
