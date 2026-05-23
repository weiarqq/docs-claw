from pathlib import Path


def test_official_docs_skill_mentions_required_workflow():
    texts = [
        Path("skills/official-docs/SKILL.md").read_text(encoding="utf-8"),
        Path("src/docs_claw/skills/official-docs/SKILL.md").read_text(encoding="utf-8"),
    ]

    for text in texts:
        assert "docs-claw search" in text
        assert "docs-claw update" in text
        assert "wiki/" in text
        assert "source_url" in text
        assert "source URLs" in text
