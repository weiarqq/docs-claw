Docs Claw
=========

Docs Claw crawls official documentation websites, converts pages to Markdown, builds an llm-wiki-style knowledge base, and provides an OpenCode skill for querying those official docs while programming.

The first implementation targets Sphinx/ReadTheDocs-style sites such as:

```text
https://ryzenai.docs.amd.com/en/latest/index.html
```

## Install

Use `uv` from the repository root:

```bash
uv run --extra dev docs-claw --help
```

Or install directly from GitHub:

```bash
uv tool install git+https://github.com/weiarqq/docs-claw.git
```

Verify the installed command:

```bash
docs-claw --help
```

For development verification:

```bash
uv run --extra dev pytest -v
```

## Register A Source

Create a shared local knowledge-base directory. Using a fixed `--root` keeps all downloaded official docs in one place, even when you call `docs-claw` from different projects.

```bash
mkdir -p ~/docs-claw-kb
```

```bash
docs-claw --root ~/docs-claw-kb add ryzenai https://ryzenai.docs.amd.com/en/latest/index.html --type sphinx
```

This creates `sources/ryzenai/source.yml` with domain and path restrictions so the crawler stays inside the official docs scope.

## One-Command Update

```bash
docs-claw --root ~/docs-claw-kb update ryzenai
```

To update the source and build the multi-way tree wiki in one command:

```bash
docs-claw --root ~/docs-claw-kb update ryzenai --tree-name "Ryzen AI"
```

Tree navigation limits are configurable:

```bash
docs-claw --root ~/docs-claw-kb update ryzenai --tree-name "Ryzen AI" --max-view-nodes 100 --max-root-nodes 500
```

You can also provide the root description:

```bash
docs-claw --root ~/docs-claw-kb update ryzenai --tree-name "Ryzen AI" --tree-description "AMD Ryzen AI software, tools, optimization, and deployment docs."
```

`update` runs crawl, HTML-to-Markdown conversion, and wiki generation. With `--tree-name`, it also writes the tree wiki. Generated artifacts are written to:

- `raw/<source-id>/`: raw HTML and crawl manifest
- `docs/<source-id>/pages/`: converted Markdown pages with `source_url` frontmatter
- `wiki/<source-id>/`: index, overview, topics, and log
- `wiki/<source-id>/tree.json`: multi-way tree wiki when `--tree-name` is used

## Search

```bash
docs-claw --root ~/docs-claw-kb search ryzenai "quantization tool usage"
```

Search results include local Markdown paths and official source URLs when available.

## Tree Wiki

`build-wiki` creates a deterministic index and topic catalog. To build the newer multi-way tree wiki structure, run:

```bash
docs-claw --root ~/docs-claw-kb build-tree ryzenai --name "Ryzen AI"
```

If you want a single command after source registration, use:

```bash
docs-claw --root ~/docs-claw-kb update ryzenai --tree-name "Ryzen AI"
```

You can provide the root description yourself:

```bash
docs-claw --root ~/docs-claw-kb build-tree ryzenai --name "Ryzen AI" --description "AMD Ryzen AI software, tools, optimization, and deployment docs."
```

If `--description` is omitted, `docs-claw` generates a short deterministic description from the source pages. Descriptions are kept short for agent context use.

Tree wiki outputs are written to:

```text
~/docs-claw-kb/wiki/ryzenai/tree.json
~/docs-claw-kb/wiki/ryzenai/tree.md
~/docs-claw-kb/wiki/ryzenai/nodes/*.md
```

The root node uses the user-provided knowledge-base name. Non-leaf nodes include `name` and `description`. Leaf references point back to original converted Markdown locations using `path`, `line`, and `limit`, plus the official `source_url`.

The builder also performs deterministic maintenance:

- Duplicate references are grouped; the highest-quality reference is marked `is_default=true`, and other matches are kept as `candidates`.
- Nodes with more than 10 default references are split into broader child nodes instead of piling up references.
- Duplicate sibling nodes are merged by normalized name.

### Multi-Turn Tree Navigation

Agents should not load the full `tree.json` into context by default. Use the navigation protocol instead:

```bash
docs-claw --root ~/docs-claw-kb tree-view ryzenai --limit 100
```

This renders a bounded view generated from `tree.json`:

```text
Ryzen AI - Installation (installation): Installation docs.
  - Linux (linux): Linux install. [leaf]
Ryzen AI - Quantization (quantization): Quantization docs. [leaf]
```

If the selected node is not a leaf, continue selecting:

```bash
docs-claw --root ~/docs-claw-kb tree-view ryzenai --root-node installation --limit 100
```

Only resolve a leaf node:

```bash
docs-claw --root ~/docs-claw-kb tree-resolve ryzenai linux
```

If a view has more nodes than the limit, use pagination:

```bash
docs-claw --root ~/docs-claw-kb tree-view ryzenai --offset 100 --limit 100
```

Inspect root split status:

```bash
docs-claw --root ~/docs-claw-kb tree-stats ryzenai
```

## Troubleshooting

### Broken Links In Official Docs

Official documentation sites sometimes contain stale links. For example, a page may link to `llm_flow.html` even though the server now returns `404 Not Found`.

`docs-claw` records failed pages in the crawl manifest and continues crawling other pages:

```text
~/docs-claw-kb/raw/<source-id>/manifest.json
```

The manifest contains an `errors` section with the failed URL, HTTP status, and referrer page that linked to it.

### SSL Or Proxy Errors

If crawling fails with an SSL EOF, proxy, or connection error, first check whether proxy environment variables are active:

```bash
env | grep -i proxy
```

Try bypassing proxy environment variables:

```bash
docs-claw --root ~/docs-claw-kb update ryzenai --ignore-proxy
```

You can also compare with `curl`:

```bash
curl -I https://ryzenai.docs.amd.com/en/latest/index.html
HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= curl -I https://ryzenai.docs.amd.com/en/latest/index.html
```

## OpenCode Skill

The repository includes `skills/official-docs/SKILL.md`. Use it when a programming task depends on official docs for an SDK, package, tool, command, or API.

### One-Click Install

For OpenCode users, the fastest install path is:

```bash
curl -fsSL https://raw.githubusercontent.com/weiarqq/docs-claw/main/install-opencode.sh | bash
```

The installer does three things:

- Installs the `docs-claw` CLI from GitHub with `uv tool install`.
- Installs the `official-docs` skill to `~/.config/opencode/skills/official-docs/SKILL.md`.
- Creates a shared knowledge-base directory at `~/docs-claw-kb`.

Restart OpenCode after installation. OpenCode loads skills at startup and does not hot-reload config-time files.

You can override the default knowledge-base directory:

```bash
DOCS_CLAW_KB_ROOT=/path/to/docs-kb curl -fsSL https://raw.githubusercontent.com/weiarqq/docs-claw/main/install-opencode.sh | bash
```

### CLI Install Then Initialize OpenCode

Install the CLI and clone this repository:

```bash
uv tool install git+https://github.com/weiarqq/docs-claw.git
git clone https://github.com/weiarqq/docs-claw.git
```

If you installed the CLI with `uv tool install`, you can install or update the OpenCode skill without cloning:

```bash
docs-claw init-opencode
```

By default this installs the skill globally and creates `~/docs-claw-kb`. You can choose a different shared knowledge-base root:

```bash
docs-claw init-opencode --kb-root /path/to/docs-kb
```

### Manual Skill Install

Install the skill globally for OpenCode:

```bash
mkdir -p ~/.config/opencode/skills/official-docs
cp docs-claw/skills/official-docs/SKILL.md ~/.config/opencode/skills/official-docs/SKILL.md
```

Restart OpenCode after copying the skill. OpenCode loads skills at startup and does not hot-reload config-time files.

If you prefer project-local registration instead of copying the skill globally, add this to your project's `opencode.json` and restart OpenCode:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["/absolute/path/to/docs-claw/skills"]
  }
}
```

The skill workflow is intentionally simple:

1. Check available sources with `docs-claw status` or `wiki/*/tree.json`.
2. Prefer `wiki/<source-id>/tree.json` to locate relevant nodes and leaf references.
3. Read referenced Markdown passages from `docs/<source-id>/pages/*.md` using `path`, `line`, and `limit`.
4. Search with `docs-claw search <source-id> "<query>"` when tree navigation is not enough.
5. Answer with official `source_url` citations.
6. Run `docs-claw update <source-id> --tree-name "<Knowledge Base Name>"` when local docs are missing or stale.

When using a shared knowledge-base directory, ask OpenCode to include the same `--root` value in commands:

```text
Use official-docs. Download this official documentation into ~/docs-claw-kb as source ryzenai: https://ryzenai.docs.amd.com/en/latest/index.html
```

```text
Use official-docs and ~/docs-claw-kb to query ryzenai: how do I use the quantization tool?
```

```text
Use official-docs and ~/docs-claw-kb to update ryzenai, then answer how Ryzen AI installation works.
```

Equivalent shell commands are:

```bash
docs-claw --root ~/docs-claw-kb add ryzenai https://ryzenai.docs.amd.com/en/latest/index.html --type sphinx
docs-claw --root ~/docs-claw-kb update ryzenai
docs-claw --root ~/docs-claw-kb search ryzenai "quantization tool"
```

## Design And Plan

- Design: `docs/superpowers/specs/2026-05-23-official-docs-claw-design.md`
- Implementation plan: `docs/superpowers/plans/2026-05-23-official-docs-claw.md`
