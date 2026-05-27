from pathlib import Path

import pytest

from docs_claw.crawler import FetchError
from docs_claw.cli import main


def test_cli_add_and_status(tmp_path: Path, capsys):
    assert main(["--root", str(tmp_path), "add", "ryzenai", "https://example.com/docs/index.html"]) == 0
    assert main(["--root", str(tmp_path), "status"]) == 0

    output = capsys.readouterr().out
    assert "Added source ryzenai" in output
    assert "ryzenai" in output


def test_cli_search_prints_results(tmp_path: Path, capsys):
    docs = tmp_path / "docs" / "ryzenai" / "pages"
    docs.mkdir(parents=True)
    (docs / "quant.md").write_text(
        """---
source_url: https://example.com/quant.html
title: Quantization Guide
---
# Quantization Guide
""",
        encoding="utf-8",
    )

    assert main(["--root", str(tmp_path), "search", "ryzenai", "quantization"]) == 0

    output = capsys.readouterr().out
    assert "Quantization Guide" in output
    assert "https://example.com/quant.html" in output


def test_cli_init_opencode_installs_skill(tmp_path: Path, capsys):
    home = tmp_path / "home"
    kb_root = tmp_path / "kb"

    assert main(["init-opencode", "--home", str(home), "--kb-root", str(kb_root)]) == 0

    output = capsys.readouterr().out
    assert "Installed OpenCode skill" in output
    assert "Restart OpenCode" in output
    assert (home / ".config" / "opencode" / "skills" / "official-docs" / "SKILL.md").exists()
    assert kb_root.exists()


def test_cli_build_tree_writes_tree_json(tmp_path: Path, capsys):
    main(["--root", str(tmp_path), "add", "ryzenai", "https://example.com/docs/index.html"])
    pages = tmp_path / "docs" / "ryzenai" / "pages"
    pages.mkdir(parents=True)
    (pages / "install.md").write_text(
        """---
source_id: ryzenai
source_url: https://example.com/install.html
title: Install
---
# Install

## Installation

Install docs.
""",
        encoding="utf-8",
    )

    assert main(["--root", str(tmp_path), "build-tree", "ryzenai", "--name", "Ryzen AI"]) == 0
    output = capsys.readouterr().out
    assert "tree.json" in output
    assert (tmp_path / "wiki" / "ryzenai" / "tree.json").exists()


def test_cli_update_can_build_tree_when_tree_name_is_provided(tmp_path: Path, monkeypatch, capsys):
    main(["--root", str(tmp_path), "add", "ryzenai", "https://example.com/docs/index.html"])

    class Crawl:
        pages_crawled = 1
        pages_failed = 0

    class Convert:
        pages_converted = 1
        pages_skipped = 0

    class Wiki:
        pages_indexed = 1

    def fake_crawl(root, source, ignore_proxy=False):
        pages = root / "docs" / source.id / "pages"
        pages.mkdir(parents=True)
        (pages / "install.md").write_text(
            """---
source_id: ryzenai
source_url: https://example.com/install.html
title: Install
---
# Install

## Installation

Install docs.
""",
            encoding="utf-8",
        )
        return Crawl()

    monkeypatch.setattr("docs_claw.cli.crawl_source", fake_crawl)
    monkeypatch.setattr("docs_claw.cli.convert_source", lambda *_args: Convert())
    monkeypatch.setattr("docs_claw.cli.build_wiki", lambda *_args: Wiki())

    assert main(["--root", str(tmp_path), "update", "ryzenai", "--tree-name", "Ryzen AI"]) == 0
    output = capsys.readouterr().out
    assert "tree nodes" in output
    assert (tmp_path / "wiki" / "ryzenai" / "tree.json").exists()


def test_cli_tree_view_resolve_and_stats(tmp_path: Path, capsys):
    main(["--root", str(tmp_path), "add", "ryzenai", "https://example.com/docs/index.html"])
    pages = tmp_path / "docs" / "ryzenai" / "pages"
    pages.mkdir(parents=True)
    (pages / "install.md").write_text(
        """---
source_id: ryzenai
source_url: https://example.com/install.html
title: Install
---
# Install

## Installation

Install docs.
""",
        encoding="utf-8",
    )
    main(["--root", str(tmp_path), "build-tree", "ryzenai", "--name", "Ryzen AI"])

    assert main(["--root", str(tmp_path), "tree-view", "ryzenai", "--limit", "5"]) == 0
    assert "Ryzen AI - Installation" in capsys.readouterr().out
    assert main(["--root", str(tmp_path), "tree-resolve", "ryzenai", "installation"]) == 0
    assert "Source: https://example.com/install.html" in capsys.readouterr().out
    assert main(["--root", str(tmp_path), "tree-stats", "ryzenai"]) == 0
    assert "Roots: 1" in capsys.readouterr().out


def test_cli_update_has_ignore_proxy_flag():
    with pytest.raises(SystemExit) as error:
        main(["update", "ryzenai", "--ignore-proxy", "--help"])

    assert error.value.code == 0


def test_cli_reports_fetch_errors_without_traceback(tmp_path: Path, monkeypatch, capsys):
    main(["--root", str(tmp_path), "add", "ryzenai", "https://example.com/docs/index.html"])

    def fail_crawl(*_args, **_kwargs):
        raise FetchError(url="https://example.com/docs/index.html", status_code=None, message="proxy TLS failed")

    monkeypatch.setattr("docs_claw.cli.crawl_source", fail_crawl)

    assert main(["--root", str(tmp_path), "update", "ryzenai"]) == 1
    output = capsys.readouterr().out
    assert "Failed to fetch https://example.com/docs/index.html" in output
    assert "proxy TLS failed" in output
    assert "--ignore-proxy" in output
