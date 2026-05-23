from pathlib import Path

from docs_claw.converter import convert_source
from docs_claw.crawler import crawl_source
from docs_claw.registry import add_source
from docs_claw.search import search_source
from docs_claw.wiki import build_wiki


def test_add_crawl_convert_build_wiki_search_end_to_end(tmp_path: Path):
    source = add_source(tmp_path, "ryzenai", "https://example.com/docs/index.html")
    pages = {
        "https://example.com/docs/index.html": """
        <article class="bd-article"><h1>Ryzen AI</h1><a href="quant.html">Quantization</a></article>
        """,
        "https://example.com/docs/quant.html": """
        <article class="bd-article"><h1>Quantization</h1><h2>Vitis AI Quantizer</h2><p>Use the quantizer package for model optimization.</p></article>
        """,
    }

    crawl = crawl_source(tmp_path, source, fetcher=pages.__getitem__)
    convert = convert_source(tmp_path, source)
    wiki = build_wiki(tmp_path, source)
    results = search_source(tmp_path, "ryzenai", "quantizer")

    assert crawl.pages_crawled == 2
    assert convert.pages_converted == 2
    assert wiki.pages_indexed == 2
    assert results
    assert results[0].source_url == "https://example.com/docs/quant.html"
