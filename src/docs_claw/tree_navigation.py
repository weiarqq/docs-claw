from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class TreeResolveError(Exception):
    pass


@dataclass(frozen=True)
class TreeDocument:
    config: dict[str, int]
    roots: list[dict[str, Any]]


def load_tree(root: Path, source_id: str) -> TreeDocument:
    path = root / "wiki" / source_id / "tree.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if "roots" in data:
        return TreeDocument(config=data.get("config", {}), roots=data["roots"])
    return TreeDocument(config={"max_view_nodes": 100, "max_root_nodes": 500}, roots=[data])


def find_node(root: Path, source_id: str, node_id: str) -> dict[str, Any]:
    document = load_tree(root, source_id)
    for tree_root in document.roots:
        found = _find_node(tree_root, node_id)
        if found:
            return found
    raise KeyError(f"tree node not found: {node_id}")


def _find_node(node: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    if node["id"] == node_id:
        return node
    for child in node.get("children", []):
        found = _find_node(child, node_id)
        if found:
            return found
    return None


def _count_nodes(node: dict[str, Any]) -> int:
    return 1 + sum(_count_nodes(child) for child in node.get("children", []))


def _is_leaf(node: dict[str, Any]) -> bool:
    return not node.get("children")


def _flatten_view_nodes(node: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    result: list[tuple[int, dict[str, Any]]] = []
    for child in node.get("children", []):
        result.append((1, child))
        for grandchild in child.get("children", []):
            result.append((2, grandchild))
    return result


def render_tree_view(
    root: Path,
    source_id: str,
    root_node_id: str = "root",
    limit: int | None = None,
    offset: int = 0,
) -> str:
    document = load_tree(root, source_id)
    limit = limit or document.config.get("max_view_nodes", 100)
    node = find_node(root, source_id, root_node_id)
    selectable = _flatten_view_nodes(node)
    window = selectable[offset : offset + limit]
    lines = [f"Showing {len(window)} of {len(selectable)} selectable nodes.", ""]
    for depth, item in window:
        marker = " [leaf]" if _is_leaf(item) else ""
        if depth == 1:
            lines.append(f"{node['name']} - {item['name']} ({item['id']}): {item['description']}{marker}")
        else:
            indent = "  " * (depth - 1)
            lines.append(f"{indent}- {item['name']} ({item['id']}): {item['description']}{marker}")
    if offset + limit < len(selectable):
        lines.extend(
            [
                "",
                "More nodes are available.",
                f"Next: docs-claw --root <kb-root> tree-view {source_id} --root-node {root_node_id} --offset {offset + limit} --limit {limit}",
            ]
        )
    return "\n".join(lines) + "\n"


def resolve_leaf_text(root: Path, source_id: str, node_id: str) -> str:
    node = find_node(root, source_id, node_id)
    if not _is_leaf(node):
        raise TreeResolveError(f"{node_id} is not a leaf; run tree-view again and select a child node")
    references = node.get("references", [])
    if not references:
        raise TreeResolveError(f"{node_id} is a leaf but has no document references")
    reference = references[0]
    path = root / reference["path"]
    lines = path.read_text(encoding="utf-8").splitlines()
    start = max(int(reference["line"]) - 1, 0)
    end = start + int(reference["limit"])
    snippet = "\n".join(lines[start:end])
    return (
        f"Source: {reference['source_url']}\n"
        f"File: {reference['path']}\n"
        f"Lines: {reference['line']}+{reference['limit']}\n\n"
        f"{snippet}\n"
    )


def tree_stats(root: Path, source_id: str) -> str:
    document = load_tree(root, source_id)
    lines = [f"Roots: {len(document.roots)}"]
    for tree_root in document.roots:
        lines.append(f"root {tree_root['name']}: {_count_nodes(tree_root)} nodes")
    return "\n".join(lines) + "\n"
