from pathlib import Path

from docs_claw.search import search_source


def test_search_source_ranks_and_returns_source_url(tmp_path: Path):
    docs = tmp_path / "docs" / "ryzenai" / "pages"
    docs.mkdir(parents=True)
    (docs / "quant.md").write_text(
        """---
source_url: https://example.com/quant.html
title: Quantization Guide
---
# Quantization Guide

Use quantization for models.
""",
        encoding="utf-8",
    )
    wiki = tmp_path / "wiki" / "ryzenai"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Index\nNo match\n", encoding="utf-8")

    results = search_source(tmp_path, "ryzenai", "quantization")

    assert results[0].title == "Quantization Guide"
    assert results[0].source_url == "https://example.com/quant.html"
    assert results[0].score > 0
