from pathlib import Path

from docs_claw.registry import SourceConfig
from docs_claw.wiki import build_wiki


def test_build_wiki_generates_index_overview_topics_and_log(tmp_path: Path):
    pages = tmp_path / "docs" / "ryzenai" / "pages"
    pages.mkdir(parents=True)
    (pages / "install.md").write_text(
        """---
source_id: ryzenai
source_url: https://example.com/install.html
title: Install
---
# Install

## Quantization

Use the quantization tool.
""",
        encoding="utf-8",
    )
    (pages / "api.md").write_text(
        """---
source_id: ryzenai
source_url: https://example.com/api.html
title: API
---
# API

## Runtime

Use the runtime package.
""",
        encoding="utf-8",
    )
    source = SourceConfig("ryzenai", "https://example.com/index.html", "sphinx", ["example.com"], ["/"], "", "")

    result = build_wiki(tmp_path, source)

    assert result.pages_indexed == 2
    assert "Install" in (tmp_path / "wiki" / "ryzenai" / "index.md").read_text()
    assert "Page count: 2" in (tmp_path / "wiki" / "ryzenai" / "overview.md").read_text()
    assert (tmp_path / "wiki" / "ryzenai" / "topics" / "quantization.md").exists()
    assert "build-wiki" in (tmp_path / "wiki" / "ryzenai" / "log.md").read_text()
