from pathlib import Path

from docs_claw.opencode import init_opencode


def test_init_opencode_installs_skill_and_creates_kb_root(tmp_path: Path):
    home = tmp_path / "home"
    kb_root = tmp_path / "kb"

    result = init_opencode(home=home, kb_root=kb_root)

    assert result.skill_path == home / ".config" / "opencode" / "skills" / "official-docs" / "SKILL.md"
    assert result.skill_path.exists()
    assert result.kb_root == kb_root
    assert result.kb_root.exists()
    assert "docs-claw search" in result.skill_path.read_text(encoding="utf-8")


def test_init_opencode_does_not_overwrite_without_force(tmp_path: Path):
    home = tmp_path / "home"
    skill_path = home / ".config" / "opencode" / "skills" / "official-docs" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("custom", encoding="utf-8")

    result = init_opencode(home=home, kb_root=tmp_path / "kb", force=False)

    assert result.skill_installed is False
    assert skill_path.read_text(encoding="utf-8") == "custom"
