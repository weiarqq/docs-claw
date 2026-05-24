import json
from pathlib import Path

import httpx

from docs_claw.crawler import FetchError, crawl_source, make_fetcher
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


def test_crawl_source_records_404_errors_and_continues(tmp_path: Path):
    pages = {
        "https://ryzenai.docs.amd.com/en/latest/index.html": """
        <article class="bd-article"><h1>Home</h1><a href="missing.html">Missing</a><a href="ok.html">OK</a></article>
        """,
        "https://ryzenai.docs.amd.com/en/latest/ok.html": """
        <article class="bd-article"><h1>OK</h1></article>
        """,
    }

    def fetcher(url: str) -> str:
        if url.endswith("missing.html"):
            raise FetchError(url=url, status_code=404, message="404 Not Found")
        return pages[url]

    result = crawl_source(tmp_path, source(), fetcher=fetcher)

    assert result.pages_crawled == 2
    assert result.pages_failed == 1
    manifest = json.loads((tmp_path / "raw" / "ryzenai" / "manifest.json").read_text())
    assert manifest["errors"] == [
        {
            "url": "https://ryzenai.docs.amd.com/en/latest/missing.html",
            "referrer": "https://ryzenai.docs.amd.com/en/latest/index.html",
            "status": 404,
            "error": "404 Not Found",
        }
    ]
    assert [page["title"] for page in manifest["pages"]] == ["Home", "OK"]


def test_make_fetcher_wraps_httpx_errors():
    def request(_url: str, trust_env: bool = True):
        raise httpx.ConnectError("proxy TLS failed")

    fetcher = make_fetcher(request=request)

    try:
        fetcher("https://example.com/docs/index.html")
    except FetchError as error:
        assert error.url == "https://example.com/docs/index.html"
        assert error.status_code is None
        assert "proxy TLS failed" in error.message
    else:
        raise AssertionError("expected FetchError")


def test_make_fetcher_can_ignore_proxy_environment():
    captured = {}

    class Response:
        text = "<html></html>"

        def raise_for_status(self):
            return None

    def request(url: str, trust_env: bool = True):
        captured["url"] = url
        captured["trust_env"] = trust_env
        return Response()

    fetcher = make_fetcher(ignore_proxy=True, request=request)

    assert fetcher("https://example.com/docs/index.html") == "<html></html>"
    assert captured == {"url": "https://example.com/docs/index.html", "trust_env": False}
