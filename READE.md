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

For development verification:

```bash
uv run --extra dev pytest -v
```

## Register A Source

```bash
uv run docs-claw add ryzenai https://ryzenai.docs.amd.com/en/latest/index.html --type sphinx
```

This creates `sources/ryzenai/source.yml` with domain and path restrictions so the crawler stays inside the official docs scope.

## One-Command Update

```bash
uv run docs-claw update ryzenai
```

`update` runs crawl, HTML-to-Markdown conversion, and wiki generation. Generated artifacts are written to:

- `raw/<source-id>/`: raw HTML and crawl manifest
- `docs/<source-id>/pages/`: converted Markdown pages with `source_url` frontmatter
- `wiki/<source-id>/`: index, overview, topics, and log

## Search

```bash
uv run docs-claw search ryzenai "quantization tool usage"
```

Search results include local Markdown paths and official source URLs when available.

## OpenCode Skill

The repository includes `skills/official-docs/SKILL.md`. Use it when a programming task depends on official docs for an SDK, package, tool, command, or API.

The skill workflow is intentionally simple:

1. Check available sources with `docs-claw status` or `wiki/*/index.md`.
2. Search with `docs-claw search <source-id> "<query>"`.
3. Read matching Markdown files under `wiki/` and `docs/`.
4. Answer with official `source_url` citations.
5. Run `docs-claw update <source-id>` when local docs are missing or stale.

## Design And Plan

- Design: `docs/superpowers/specs/2026-05-23-official-docs-claw-design.md`
- Implementation plan: `docs/superpowers/plans/2026-05-23-official-docs-claw.md`
