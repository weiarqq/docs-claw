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
