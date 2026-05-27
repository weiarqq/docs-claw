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

1. Inspect available sources with `docs-claw status`.
2. Use `docs-claw tree-view <source-id> --limit 100` to show a bounded tree view generated from `tree.json`.
3. Choose the best node id for the user's question. If the selected node is not a leaf, run `docs-claw tree-view <source-id> --root-node <node-id> --limit 100` and choose again.
4. Do not read source passages until a leaf node is selected.
5. Resolve the final leaf with `docs-claw tree-resolve <source-id> <node-id>`.
6. Answer using the returned text and cite `source_url`.
7. If the docs are missing or stale, run or suggest `docs-claw update <source-id> --tree-name "<Knowledge Base Name>"` before relying on old content.

## Query Pattern

```bash
docs-claw status
docs-claw --root ~/docs-claw-kb update ryzenai --tree-name "Ryzen AI"
docs-claw --root ~/docs-claw-kb tree-view ryzenai --limit 100
docs-claw --root ~/docs-claw-kb tree-view ryzenai --root-node quantization --limit 100
docs-claw --root ~/docs-claw-kb tree-resolve ryzenai quantization
```

Use `docs-claw search ryzenai "query"` only when tree navigation is insufficient.

## Common Mistakes

- Do not answer from memory when a local official documentation source exists.
- Do not crawl arbitrary websites from the skill. Use `docs-claw add` and `docs-claw update` for source lifecycle.
- Do not cite only local file paths. Include official source URLs when present.
- Do not load the full `tree.json` into context by default. Use `tree-view` and `tree-resolve`.
- Do not resolve a non-leaf node. Continue `tree-view` selection until a leaf is selected.
