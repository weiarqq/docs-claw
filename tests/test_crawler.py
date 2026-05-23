import json
from pathlib import Path

from docs_claw.crawler import crawl_source
from docs_claw.registry import SourceConfig


def source() -> SourceConfig:
    return SourceConfig(
        id="ryzenai",
        url="https://ryzenai.docs.amd.com/en/latest/index.html",
        type="sphinx",
        allowed_domains=["ryzenai.docs.amd.com"],
        allowed_path_prefixes=["/en/latest/"],
        created_at="2026-05-23T00:00:00Z",
        updated_at="2026-05-23T00:00:00Z",
    )


def test_crawl_source_writes_scoped_pages_and_manifest(tmp_path: Path):
    pages = {
        "https://ryzenai.docs.amd.com/en/latest/index.html": """
        <article class="bd-article"><h1>Home</h1><a href="install.html">Install</a><a href="https://example.com/out.html">Out</a></article>
        """,
        "https://ryzenai.docs.amd.com/en/latest/install.html": """
        <article class="bd-article"><h1>Install</h1><a href="api.html">API</a></article>
        """,
        "https://ryzenai.docs.amd.com/en/latest/api.html": """
        <article class="bd-article"><h1>API</h1></article>
        """,
    }

    result = crawl_source(tmp_path, source(), fetcher=pages.__getitem__)

    assert result.pages_crawled == 3
    manifest = json.loads((tmp_path / "raw" / "ryzenai" / "manifest.json").read_text())
    assert [page["title"] for page in manifest["pages"]] == ["Home", "Install", "API"]
    for page in manifest["pages"]:
        assert (tmp_path / page["raw_path"]).exists()
