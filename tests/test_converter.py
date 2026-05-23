import json
from pathlib import Path

from docs_claw.converter import convert_source
from docs_claw.registry import SourceConfig


def test_convert_source_writes_markdown_with_frontmatter(tmp_path: Path):
    raw_dir = tmp_path / "raw" / "ryzenai" / "pages"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "page.html"
    raw_file.write_text(
        "<article class='bd-article'><h1>Install</h1><p>Use Ryzen AI.</p><pre><code>pip install</code></pre></article>",
        encoding="utf-8",
    )
    (tmp_path / "raw" / "ryzenai" / "manifest.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "url": "https://example.com/docs/install.html",
                        "raw_path": "raw/ryzenai/pages/page.html",
                        "title": "Install",
                        "content_hash": "abc123",
                        "fetched_at": "2026-05-23T00:00:00Z",
                        "status": 200,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source = SourceConfig("ryzenai", "https://example.com/docs/index.html", "sphinx", ["example.com"], ["/docs/"], "", "")

    result = convert_source(tmp_path, source)

    assert result.pages_converted == 1
    output = tmp_path / "docs" / "ryzenai" / "pages" / "page.md"
    text = output.read_text(encoding="utf-8")
    assert "source_url: https://example.com/docs/install.html" in text
    assert "# Install" in text
    assert "Use Ryzen AI." in text
