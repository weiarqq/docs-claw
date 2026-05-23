#!/usr/bin/env bash
set -eu

REPO_URL="git+https://github.com/weiarqq/docs-claw.git"
KB_ROOT="${DOCS_CLAW_KB_ROOT:-$HOME/docs-claw-kb}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found. Install it from https://docs.astral.sh/uv/ and run this script again." >&2
  exit 1
fi

echo "Installing docs-claw from ${REPO_URL}"
uv tool install --force "${REPO_URL}"

echo "Installing the official-docs OpenCode skill"
docs-claw init-opencode --kb-root "${KB_ROOT}" --force

echo ""
echo "docs-claw is ready. Restart OpenCode so it reloads skills."
echo ""
echo "Example OpenCode prompts:"
echo "  Use official-docs. Download this official documentation into ${KB_ROOT} as source ryzenai: https://ryzenai.docs.amd.com/en/latest/index.html"
echo "  Use official-docs and ${KB_ROOT} to query ryzenai: how do I use the quantization tool?"
