from docs_claw.adapters.sphinx import (
    extract_links,
    extract_main_content,
    extract_title,
    is_allowed_url,
    normalize_url,
)
from docs_claw.registry import SourceConfig


SOURCE = SourceConfig(
    id="ryzenai",
    url="https://ryzenai.docs.amd.com/en/latest/index.html",
    type="sphinx",
    allowed_domains=["ryzenai.docs.amd.com"],
    allowed_path_prefixes=["/en/latest/"],
    created_at="2026-05-23T00:00:00Z",
    updated_at="2026-05-23T00:00:00Z",
)


def test_normalize_url_resolves_relative_links_and_drops_fragments():
    assert normalize_url(SOURCE.url, "guide/install.html#setup") == (
        "https://ryzenai.docs.amd.com/en/latest/guide/install.html"
    )


def test_is_allowed_url_enforces_domain_and_prefix():
    assert is_allowed_url(SOURCE, "https://ryzenai.docs.amd.com/en/latest/guide.html")
    assert not is_allowed_url(SOURCE, "https://ryzenai.docs.amd.com/en/stable/guide.html")
    assert not is_allowed_url(SOURCE, "https://example.com/en/latest/guide.html")


def test_extract_title_prefers_h1():
    html = "<html><title>Site</title><body><h1>Install Ryzen AI</h1></body></html>"
    assert extract_title(html) == "Install Ryzen AI"


def test_extract_main_content_uses_sphinx_article():
    html = """
    <html><body><nav>Nav</nav><article class="bd-article"><h1>Title</h1><p>Body</p></article></body></html>
    """
    assert "Body" in extract_main_content(html)
    assert "Nav" not in extract_main_content(html)


def test_extract_links_returns_allowed_links_only():
    html = """
    <a href="guide.html">Guide</a>
    <a href="https://example.com/out.html">Out</a>
    <a href="#local">Local</a>
    """
    assert extract_links(SOURCE, SOURCE.url, html) == [
        "https://ryzenai.docs.amd.com/en/latest/guide.html"
    ]
