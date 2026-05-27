import json
from pathlib import Path

import pytest

from docs_claw.tree_navigation import TreeResolveError, render_tree_view, resolve_leaf_text, tree_stats


def write_tree(root: Path) -> None:
    wiki = root / "wiki" / "ryzenai"
    wiki.mkdir(parents=True)
    (wiki / "tree.json").write_text(
        json.dumps(
            {
                "version": 2,
                "config": {"max_view_nodes": 3, "max_root_nodes": 500},
                "roots": [
                    {
                        "id": "root",
                        "name": "Ryzen AI",
                        "description": "Root docs.",
                        "children": [
                            {
                                "id": "install",
                                "name": "Installation",
                                "description": "Install docs.",
                                "children": [
                                    {
                                        "id": "linux",
                                        "name": "Linux",
                                        "description": "Linux install.",
                                        "children": [],
                                        "references": [
                                            {
                                                "title": "Linux Install",
                                                "path": "docs/ryzenai/pages/linux.md",
                                                "source_url": "https://example.com/linux.html",
                                                "line": 3,
                                                "limit": 2,
                                                "quality": 1.0,
                                                "is_default": True,
                                                "candidates": [],
                                            }
                                        ],
                                    }
                                ],
                                "references": [],
                            },
                            {"id": "quant", "name": "Quantization", "description": "Quant docs.", "children": [], "references": []},
                            {"id": "runtime", "name": "Runtime", "description": "Runtime docs.", "children": [], "references": []},
                            {"id": "api", "name": "API", "description": "API docs.", "children": [], "references": []},
                        ],
                        "references": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    docs = root / "docs" / "ryzenai" / "pages"
    docs.mkdir(parents=True)
    (docs / "linux.md").write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8")


def test_render_tree_view_outputs_root_and_first_two_levels(tmp_path: Path):
    write_tree(tmp_path)

    view = render_tree_view(tmp_path, "ryzenai", root_node_id="root", limit=10)

    assert "Ryzen AI - Installation (install): Install docs." in view
    assert "  - Linux (linux): Linux install. [leaf]" in view
    assert "- Quantization (quant): Quant docs. [leaf]" in view


def test_render_tree_view_paginates_selectable_nodes(tmp_path: Path):
    write_tree(tmp_path)

    view = render_tree_view(tmp_path, "ryzenai", root_node_id="root", limit=2, offset=0)

    assert "Showing 2 of 5 selectable nodes." in view
    assert "--offset 2 --limit 2" in view
    assert "Installation" in view
    assert "Quantization" not in view


def test_resolve_leaf_text_returns_text_for_leaf(tmp_path: Path):
    write_tree(tmp_path)

    text = resolve_leaf_text(tmp_path, "ryzenai", "linux")

    assert "Source: https://example.com/linux.html" in text
    assert "File: docs/ryzenai/pages/linux.md" in text
    assert "Lines: 3+2" in text
    assert "line3\nline4" in text


def test_resolve_leaf_text_rejects_non_leaf(tmp_path: Path):
    write_tree(tmp_path)

    with pytest.raises(TreeResolveError, match="not a leaf"):
        resolve_leaf_text(tmp_path, "ryzenai", "install")


def test_tree_stats_reports_root_and_node_counts(tmp_path: Path):
    write_tree(tmp_path)

    stats = tree_stats(tmp_path, "ryzenai")

    assert "Roots: 1" in stats
    assert "root Ryzen AI: 6 nodes" in stats
