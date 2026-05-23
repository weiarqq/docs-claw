from pathlib import Path


def test_official_docs_skill_mentions_required_workflow():
    text = Path("skills/official-docs/SKILL.md").read_text(encoding="utf-8")

    assert "docs-claw search" in text
    assert "docs-claw update" in text
    assert "wiki/" in text
    assert "source_url" in text
    assert "source URLs" in text
