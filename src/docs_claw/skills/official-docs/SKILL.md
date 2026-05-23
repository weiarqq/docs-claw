---
name: official-docs
description: Use when programming requires checking locally ingested official documentation for tools, packages, APIs, SDKs, commands, examples, or version-specific behavior.
---

# Official Docs

## Overview

Use the local `docs-claw` knowledge base before answering implementation questions about external tools, packages, SDKs, APIs, and official examples. Prefer official docs in `wiki/` and `docs/` over memory.

## When To Use

- The user asks how to use a tool, package, API, SDK, command, or framework covered by an ingested official documentation source.
- You are about to write code that depends on version-specific official behavior.
- You need examples, installation steps, configuration keys, CLI flags, or package usage from official docs.

## Workflow

1. Inspect available sources with `docs-claw status` or by checking `wiki/*/index.md`.
2. Search the likely source with `docs-claw search <source-id> "<query>"`.
3. Read the top matching `wiki/` topic/index pages and generated `docs/<source-id>/pages/*.md` pages.
4. Answer using the local documentation. Include `source_url` values or source URLs from the relevant pages.
5. If the docs are missing or stale, run or suggest `docs-claw update <source-id>` before relying on old content.

## Query Pattern

```bash
docs-claw status
docs-claw search ryzenai "quantization tool usage"
```

Then read the matching Markdown files and cite their `source_url` fields in the answer.

## Common Mistakes

- Do not answer from memory when a local official documentation source exists.
- Do not crawl arbitrary websites from the skill. Use `docs-claw add` and `docs-claw update` for source lifecycle.
- Do not cite only local file paths. Include official source URLs when present.
