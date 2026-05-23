from pathlib import Path

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
