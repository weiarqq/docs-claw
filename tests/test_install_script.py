from pathlib import Path


def test_install_script_contains_github_install_and_init_command():
    text = Path("install-opencode.sh").read_text(encoding="utf-8")

    assert "git+https://github.com/weiarqq/docs-claw.git" in text
    assert "uv tool install --force" in text
    assert "docs-claw init-opencode --kb-root" in text
    assert "Restart OpenCode" in text
