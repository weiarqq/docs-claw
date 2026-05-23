from pathlib import Path

from docs_claw.registry import add_source, list_sources, load_source


def test_add_source_creates_scoped_config(tmp_path: Path):
    source = add_source(
        tmp_path,
        "ryzenai",
        "https://ryzenai.docs.amd.com/en/latest/index.html",
        "sphinx",
    )

    assert source.id == "ryzenai"
    assert source.type == "sphinx"
    assert source.allowed_domains == ["ryzenai.docs.amd.com"]
    assert source.allowed_path_prefixes == ["/en/latest/"]
    assert (tmp_path / "sources" / "ryzenai" / "source.yml").exists()


def test_load_source_reads_config(tmp_path: Path):
    add_source(tmp_path, "ryzenai", "https://ryzenai.docs.amd.com/en/latest/index.html")

    source = load_source(tmp_path, "ryzenai")

    assert source.url == "https://ryzenai.docs.amd.com/en/latest/index.html"
    assert source.created_at
    assert source.updated_at


def test_list_sources_returns_registered_sources(tmp_path: Path):
    add_source(tmp_path, "ryzenai", "https://ryzenai.docs.amd.com/en/latest/index.html")
    add_source(tmp_path, "other", "https://example.com/docs/index.html")

    assert [source.id for source in list_sources(tmp_path)] == ["other", "ryzenai"]
