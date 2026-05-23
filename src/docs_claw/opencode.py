from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from docs_claw.paths import ensure_dir


@dataclass(frozen=True)
class OpenCodeInitResult:
    skill_path: Path
    kb_root: Path
    skill_installed: bool


def _bundled_skill_text() -> str:
    return (
        resources.files("docs_claw")
        .joinpath("skills/official-docs/SKILL.md")
        .read_text(encoding="utf-8")
    )


def init_opencode(
    home: Path | None = None,
    kb_root: Path | None = None,
    force: bool = True,
) -> OpenCodeInitResult:
    user_home = (home or Path.home()).expanduser()
    docs_root = (kb_root or (user_home / "docs-claw-kb")).expanduser()
    skill_path = user_home / ".config" / "opencode" / "skills" / "official-docs" / "SKILL.md"

    ensure_dir(docs_root)
    ensure_dir(skill_path.parent)

    installed = False
    if force or not skill_path.exists():
        skill_path.write_text(_bundled_skill_text(), encoding="utf-8")
        installed = True

    return OpenCodeInitResult(
        skill_path=skill_path,
        kb_root=docs_root,
        skill_installed=installed,
    )
