import json
from pathlib import Path

from docs_claw.registry import SourceConfig
from docs_claw.tree_wiki import build_tree_wiki


def source() -> SourceConfig:
    return SourceConfig("ryzenai", "https://example.com/index.html", "sphinx", ["example.com"], ["/"], "", "")


def write_page(root: Path, name: str, title: str, source_url: str, body: str) -> Path:
    pages = root / "docs" / "ryzenai" / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    path = pages / name
    path.write_text(
        f"""---
source_id: ryzenai
source_url: {source_url}
title: {title}
---
{body}
""",
        encoding="utf-8",
    )
    return path


def load_tree(root: Path) -> dict:
    return json.loads((root / "wiki" / "ryzenai" / "tree.json").read_text(encoding="utf-8"))


def load_primary_root(root: Path) -> dict:
    return load_tree(root)["roots"][0]


def find_node(node: dict, name: str) -> dict | None:
    if node["name"] == name:
        return node
    for child in node.get("children", []):
        found = find_node(child, name)
        if found:
            return found
    return None


def leaf_reference_count(node: dict) -> int:
    total = len(node.get("references", []))
    for child in node.get("children", []):
        total += leaf_reference_count(child)
    return total


def test_build_tree_wiki_writes_root_and_leaf_references(tmp_path: Path):
    write_page(
        tmp_path,
        "install.md",
        "Install",
        "https://example.com/install.html",
        "# Install\n\n## Installation\n\nInstall Ryzen AI.\n",
    )
    write_page(
        tmp_path,
        "quant.md",
        "Quantization",
        "https://example.com/quant.html",
        "# Quantization\n\n## Quantization\n\nUse quantization.\n",
    )

    result = build_tree_wiki(tmp_path, source(), name="Ryzen AI", description="AMD Ryzen AI documentation tree.")

    tree = load_tree(tmp_path)
    assert result.nodes_written >= 2
    assert tree["version"] == 2
    assert tree["config"] == {"max_view_nodes": 100, "max_root_nodes": 500}
    root_node = tree["roots"][0]
    assert root_node["name"] == "Ryzen AI"
    assert root_node["description"] == "AMD Ryzen AI documentation tree."
    installation = find_node(root_node, "Installation")
    assert installation is not None
    reference = installation["references"][0]
    assert reference["path"] == "docs/ryzenai/pages/install.md"
    assert reference["source_url"] == "https://example.com/install.html"
    assert reference["line"] == 8
    assert reference["limit"] > 0
    assert reference["quality"] > 0
    assert reference["is_default"] is True
    assert (tmp_path / "wiki" / "ryzenai" / "tree.md").exists()
    assert (tmp_path / "wiki" / "ryzenai" / "nodes" / "installation.md").exists()


def test_build_tree_wiki_generates_short_description_when_missing(tmp_path: Path):
    write_page(tmp_path, "api.md", "API", "https://example.com/api.html", "# API\n\n## Runtime\n\nRuntime package.\n")

    build_tree_wiki(tmp_path, source(), name="Ryzen AI")

    description = load_primary_root(tmp_path)["description"]
    assert description
    assert len(description) <= 100


def test_build_tree_wiki_deduplicates_references_and_keeps_best_default(tmp_path: Path):
    write_page(
        tmp_path,
        "short.md",
        "Quantization Guide",
        "https://example.com/quant.html",
        "# Quantization Guide\n\n## Quantization\n\nShort.\n",
    )
    write_page(
        tmp_path,
        "rich.md",
        "Quantization Guide",
        "https://example.com/quant.html",
        "# Quantization Guide\n\n## Quantization\n\nDetailed usage.\n\n```python\nprint('quant')\n```\n",
    )

    build_tree_wiki(tmp_path, source(), name="Ryzen AI")

    node = find_node(load_primary_root(tmp_path), "Quantization")

    assert node is not None
    assert len(node["references"]) == 1
    assert node["references"][0]["path"] == "docs/ryzenai/pages/rich.md"
    assert node["references"][0]["candidates"][0]["path"] == "docs/ryzenai/pages/short.md"


def test_build_tree_wiki_splits_nodes_with_more_than_ten_references(tmp_path: Path):
    for index in range(12):
        write_page(
            tmp_path,
            f"quant-{index}.md",
            f"Quantization {index}",
            f"https://example.com/quant-{index}.html",
            f"# Quantization {index}\n\n## Quantization\n\nExample {index}.\n",
        )

    build_tree_wiki(tmp_path, source(), name="Ryzen AI")
    node = find_node(load_primary_root(tmp_path), "Quantization")

    assert node is not None
    assert len(node["references"]) == 0
    assert len(node["children"]) >= 2
    assert all(len(child.get("references", [])) <= 10 for child in node["children"])
    assert leaf_reference_count(node) == 12


def test_build_tree_wiki_merges_duplicate_sibling_nodes(tmp_path: Path):
    write_page(tmp_path, "a.md", "A", "https://example.com/a.html", "# A\n\n## Runtime\n\nRuntime A.\n")
    write_page(tmp_path, "b.md", "B", "https://example.com/b.html", "# B\n\n## runtime\n\nRuntime B.\n")

    build_tree_wiki(tmp_path, source(), name="Ryzen AI")
    tree = load_primary_root(tmp_path)
    runtime_nodes = [child for child in tree["children"] if child["name"].lower() == "runtime"]

    assert len(runtime_nodes) == 1
    assert len(runtime_nodes[0]["references"]) == 2


def test_build_tree_wiki_cleans_sphinx_heading_anchor_noise(tmp_path: Path):
    write_page(
        tmp_path,
        "install.md",
        "Install[#](#install \"Link to this heading\")",
        "https://example.com/install.html",
        "# Install[#](#install \"Link to this heading\")\n\n## Installation Steps[#](#installation-steps \"Link to this heading\")\n\nInstall docs.\n",
    )

    build_tree_wiki(tmp_path, source(), name="Ryzen AI")
    node = load_primary_root(tmp_path)["children"][0]

    assert node["name"] == "Installation Steps"
    assert "[#]" not in node["description"]
    assert "Link To This Heading" not in node["description"]
    assert node["references"][0]["title"] == "Install"


def test_build_tree_wiki_cleans_markdown_links_and_keeps_heading_line(tmp_path: Path):
    write_page(
        tmp_path,
        "faq.md",
        "FAQ",
        "https://example.com/faq.html",
        "# FAQ\n\n## [Windows AI APIs](#id1)[#](#windows-ai-apis \"Link to this heading\")\n\nQuestion.\n",
    )

    build_tree_wiki(tmp_path, source(), name="Ryzen AI")
    node = load_primary_root(tmp_path)["children"][0]

    assert node["name"] == "Windows AI APIs"
    assert node["id"] == "windows-ai-apis"
    assert node["references"][0]["line"] == 8


def test_build_tree_wiki_splits_large_roots_by_top_level_nodes(tmp_path: Path):
    for index in range(5):
        write_page(
            tmp_path,
            f"topic-{index}.md",
            f"Topic {index}",
            f"https://example.com/topic-{index}.html",
            f"# Topic {index}\n\n## Topic {index}\n\nContent.\n",
        )

    build_tree_wiki(tmp_path, source(), name="Ryzen AI", max_root_nodes=3)
    tree = load_tree(tmp_path)

    assert tree["config"]["max_root_nodes"] == 3
    assert len(tree["roots"]) == 3
    assert [root["name"] for root in tree["roots"]] == ["Ryzen AI", "Ryzen AI 2", "Ryzen AI 3"]
    assert all(len(root["children"]) <= 2 for root in tree["roots"])
