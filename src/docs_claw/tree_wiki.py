from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docs_claw.paths import ensure_dir
from docs_claw.registry import SourceConfig


MAX_DESCRIPTION = 100
MAX_REFERENCES_PER_NODE = 10
DEFAULT_MAX_VIEW_NODES = 100
DEFAULT_MAX_ROOT_NODES = 500


@dataclass(frozen=True)
class TreeWikiResult:
    nodes_written: int
    references_indexed: int
    tree_path: Path


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "untitled"


def _normalize_name(text: str) -> str:
    cleaned = _clean_heading_text(text)
    words = re.sub(r"\s+", " ", cleaned.strip()).split(" ")
    return " ".join(_normalize_word(word) for word in words)


def _normalize_word(word: str) -> str:
    if word.isupper():
        return word
    if any(character.isupper() for character in word[1:]):
        return word
    return word.title()


def _clean_heading_text(text: str) -> str:
    text = re.sub(r"\[#\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    try:
        _start, frontmatter, body = text.split("---\n", 2)
    except ValueError:
        return {}, text
    meta: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, body


def _fallback_description(source: SourceConfig, pages: list[dict[str, Any]]) -> str:
    headings: list[str] = []
    for page in pages:
        headings.extend(page["headings"][:2])
    prominent = ", ".join(dict.fromkeys(headings[:4]))
    if prominent:
        description = f"{source.id} documentation knowledge base covering {prominent}."
    else:
        description = f"{source.id} documentation knowledge base with {len(pages)} source pages."
    return description[:MAX_DESCRIPTION]


def _heading_lines(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for index, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            result.setdefault(_clean_heading_text(line.lstrip("# ").strip()), index)
    return result


def _parse_page(root: Path, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    headings = [_clean_heading_text(line.lstrip("# ").strip()) for line in body.splitlines() if line.startswith("## ")]
    primary = headings[0] if headings else meta.get("title", path.stem)
    title = _clean_heading_text(meta.get("title", path.stem))
    return {
        "path": path,
        "relative_path": str(path.relative_to(root)),
        "title": title,
        "source_url": meta.get("source_url", ""),
        "body": body,
        "headings": headings,
        "primary_heading": _normalize_name(primary),
        "line_by_heading": _heading_lines(text),
    }


def _quality(page: dict[str, Any]) -> float:
    body = page["body"]
    heading_score = len(page["headings"]) * 0.2
    code_score = body.count("```") * 0.3
    length_score = min(len(body) / 2000, 1.0)
    source_score = 0.2 if page["source_url"] else 0.0
    return round(heading_score + code_score + length_score + source_score, 3)


def _reference(page: dict[str, Any]) -> dict[str, Any]:
    heading = page["primary_heading"]
    return {
        "doc_id": _slug(f"{page['title']}-{page['source_url']}-{page['relative_path']}"),
        "title": page["title"],
        "path": page["relative_path"],
        "source_url": page["source_url"],
        "line": page["line_by_heading"].get(heading, 1),
        "limit": min(max(len(page["body"].splitlines()), 20), 200),
        "quality": _quality(page),
        "is_default": True,
        "candidates": [],
    }


def _dedupe(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for reference in references:
        key = reference["source_url"] or _slug(reference["title"])
        groups.setdefault(key, []).append(reference)
    result: list[dict[str, Any]] = []
    for group in groups.values():
        sorted_group = sorted(group, key=lambda ref: (-ref["quality"], ref["path"]))
        best = dict(sorted_group[0])
        best["is_default"] = True
        best["candidates"] = []
        for candidate in sorted_group[1:]:
            item = dict(candidate)
            item["is_default"] = False
            item.pop("candidates", None)
            best["candidates"].append(item)
        result.append(best)
    return sorted(result, key=lambda ref: ref["title"])


def _node(node_id: str, name: str, description: str) -> dict[str, Any]:
    return {
        "id": node_id,
        "name": name,
        "description": description[:MAX_DESCRIPTION],
        "children": [],
        "references": [],
    }


def _split_if_needed(node: dict[str, Any]) -> None:
    references = node.get("references", [])
    if len(references) <= MAX_REFERENCES_PER_NODE:
        return
    node["references"] = []
    for index in range(0, len(references), MAX_REFERENCES_PER_NODE):
        chunk = references[index : index + MAX_REFERENCES_PER_NODE]
        child_name = f"{node['name']} {index // MAX_REFERENCES_PER_NODE + 1}"
        child = _node(_slug(child_name), child_name, f"References related to {child_name}.")
        child["references"] = chunk
        node["children"].append(child)


def _write_markdown(root: Path, source_id: str, roots: list[dict[str, Any]]) -> int:
    wiki_dir = ensure_dir(root / "wiki" / source_id)
    nodes_dir = ensure_dir(wiki_dir / "nodes")
    for path in nodes_dir.glob("*.md"):
        path.unlink()

    lines: list[str] = []
    count = 0

    def visit(node: dict[str, Any], depth: int = 0) -> None:
        nonlocal count
        count += 1
        indent = "  " * depth
        lines.append(f"{indent}- {node['name']}: {node['description']}")
        node_lines = [f"# {node['name']}", "", node["description"], ""]
        if node.get("references"):
            node_lines.extend(["## Default References", ""])
            for reference in node["references"]:
                node_lines.append(
                    f"- `{reference['path']}` lines {reference['line']}+{reference['limit']} - {reference['source_url']}"
                )
        (nodes_dir / f"{node['id']}.md").write_text("\n".join(node_lines) + "\n", encoding="utf-8")
        for child in node.get("children", []):
            visit(child, depth + 1)

    for tree in roots:
        visit(tree)
    (wiki_dir / "tree.md").write_text("# Tree Wiki\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return count


def _count_nodes(node: dict[str, Any]) -> int:
    return 1 + sum(_count_nodes(child) for child in node.get("children", []))


def _split_roots(root_node: dict[str, Any], max_root_nodes: int) -> list[dict[str, Any]]:
    if _count_nodes(root_node) <= max_root_nodes:
        return [root_node]
    capacity = max(1, max_root_nodes - 1)
    roots: list[dict[str, Any]] = []
    children = root_node["children"]
    for index in range(0, len(children), capacity):
        chunk = children[index : index + capacity]
        suffix = "" if index == 0 else f" {len(roots) + 1}"
        new_root = _node(
            "root" if index == 0 else f"root-{len(roots) + 1}",
            f"{root_node['name']}{suffix}",
            root_node["description"],
        )
        new_root["children"] = chunk
        roots.append(new_root)
    return roots


def build_tree_wiki(
    root: Path,
    source: SourceConfig,
    name: str,
    description: str | None = None,
    max_view_nodes: int = DEFAULT_MAX_VIEW_NODES,
    max_root_nodes: int = DEFAULT_MAX_ROOT_NODES,
) -> TreeWikiResult:
    pages_dir = root / "docs" / source.id / "pages"
    if not pages_dir.exists():
        raise FileNotFoundError(f"converted docs not found: {pages_dir}")
    pages = [_parse_page(root, path) for path in sorted(pages_dir.glob("*.md"))]
    root_node = _node("root", name, description or _fallback_description(source, pages))

    by_topic: dict[str, list[dict[str, Any]]] = {}
    for page in pages:
        by_topic.setdefault(page["primary_heading"], []).append(_reference(page))

    for topic, references in sorted(by_topic.items()):
        topic_node = _node(_slug(topic), topic, f"Documentation references for {topic}.")
        topic_node["references"] = _dedupe(references)
        _split_if_needed(topic_node)
        root_node["children"].append(topic_node)

    wiki_dir = ensure_dir(root / "wiki" / source.id)
    roots = _split_roots(root_node, max_root_nodes=max_root_nodes)
    envelope = {
        "version": 2,
        "config": {
            "max_view_nodes": max_view_nodes,
            "max_root_nodes": max_root_nodes,
        },
        "roots": roots,
    }
    tree_path = wiki_dir / "tree.json"
    tree_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    nodes_written = _write_markdown(root, source.id, roots)
    references_indexed = sum(_reference_count(tree) for tree in roots)
    return TreeWikiResult(nodes_written=nodes_written, references_indexed=references_indexed, tree_path=tree_path)


def _reference_count(node: dict[str, Any]) -> int:
    return len(node.get("references", [])) + sum(_reference_count(child) for child in node.get("children", []))
