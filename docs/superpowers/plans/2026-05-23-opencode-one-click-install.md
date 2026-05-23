# OpenCode One-Click Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-command installation path that installs the `docs-claw` CLI, installs the OpenCode `official-docs` skill, creates a shared knowledge-base directory, and documents the workflow.

**Architecture:** Add a small `docs_claw.opencode` module responsible for copying the bundled skill into OpenCode's global skill directory and creating the default knowledge-base root. Expose it through `docs-claw init-opencode`, and add a repository-level `install-opencode.sh` script that installs the package from GitHub and invokes the CLI initializer.

**Tech Stack:** Python standard library, argparse, setuptools package data, POSIX shell, pytest.

---

## File Structure

- Create `src/docs_claw/opencode.py`: OpenCode skill installation helper.
- Modify `src/docs_claw/cli.py`: add `init-opencode` command.
- Modify `pyproject.toml`: include bundled skill data.
- Create `install-opencode.sh`: one-click installer for GitHub users.
- Modify `READE.md`: document one-click installer and `init-opencode`.
- Create `tests/test_opencode_init.py`: install helper tests.
- Modify `tests/test_cli.py`: CLI test for `init-opencode`.
- Create `tests/test_install_script.py`: shell script existence/content test.

## Tasks

### Task 1: OpenCode Installer Helper

**Files:**
- Create: `src/docs_claw/opencode.py`
- Create: `tests/test_opencode_init.py`

- [ ] Write a test that calls `init_opencode(home=tmp_path / "home", kb_root=tmp_path / "kb")`.
- [ ] Assert it creates `home/.config/opencode/skills/official-docs/SKILL.md`.
- [ ] Assert it creates the requested knowledge-base root.
- [ ] Implement `OpenCodeInitResult` and `init_opencode()` using `importlib.resources` to read the bundled skill.
- [ ] Run `uv run --extra dev pytest tests/test_opencode_init.py -v` and expect PASS.

### Task 2: CLI Command

**Files:**
- Modify: `src/docs_claw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] Add a test for `main(["init-opencode", "--home", str(home), "--kb-root", str(kb)])`.
- [ ] Implement parser support for `init-opencode` with `--home`, `--kb-root`, and `--force`.
- [ ] Print installed skill path, knowledge-base root, and restart reminder.
- [ ] Run `uv run --extra dev pytest tests/test_cli.py -v` and expect PASS.

### Task 3: Package Skill Data

**Files:**
- Modify: `pyproject.toml`
- Move/copy: `skills/official-docs/SKILL.md` to `src/docs_claw/skills/official-docs/SKILL.md`
- Modify: `tests/test_skill_file.py`

- [ ] Add package data config for `docs_claw.skills.official-docs/SKILL.md`.
- [ ] Keep repository skill at `skills/official-docs/SKILL.md` for source users.
- [ ] Test both skill files contain required workflow text.
- [ ] Run `uv run --extra dev pytest tests/test_skill_file.py tests/test_opencode_init.py -v` and expect PASS.

### Task 4: One-Click Shell Installer

**Files:**
- Create: `install-opencode.sh`
- Create: `tests/test_install_script.py`

- [ ] Add shell script with `set -eu`.
- [ ] Check `uv` exists and print a clear install instruction if missing.
- [ ] Run `uv tool install --force git+https://github.com/weiarqq/docs-claw.git`.
- [ ] Run `docs-claw init-opencode --kb-root "$HOME/docs-claw-kb" --force`.
- [ ] Print example OpenCode prompts and restart reminder.
- [ ] Add a test that verifies the script contains the GitHub install URL and init command.
- [ ] Run `bash -n install-opencode.sh` and `uv run --extra dev pytest tests/test_install_script.py -v`.

### Task 5: README Update And Verification

**Files:**
- Modify: `READE.md`

- [ ] Add one-click install at the top of the OpenCode section.
- [ ] Document `docs-claw init-opencode` for users who already installed the CLI.
- [ ] Keep manual install as fallback.
- [ ] Run `uv run --extra dev pytest -v`.
- [ ] Run `uv run --extra dev python -m docs_claw.cli init-opencode --help`.
- [ ] Run `bash -n install-opencode.sh`.

## Self-Review

- Spec coverage: one-click script, CLI initializer, skill packaging, README usage, and verification are covered.
- Placeholder scan: no placeholders remain.
- Type consistency: `init_opencode`, `OpenCodeInitResult`, `--kb-root`, and `--home` are consistent across tasks.
