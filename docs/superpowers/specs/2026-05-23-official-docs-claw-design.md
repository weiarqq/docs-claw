# Official Docs Claw Design

## Goal

Build a local toolchain that ingests official documentation websites, converts their pages to clean Markdown, maintains an llm-wiki-style knowledge base, supports one-command manual updates, and provides an OpenCode skill that programming agents can use to query the local official-documentation knowledge base.

The first target is Sphinx/ReadTheDocs-style documentation such as `https://ryzenai.docs.amd.com/en/latest/index.html`. The implementation should keep adapter boundaries clear so other static documentation sites can be supported later.

## Recommended Approach

Use a Python CLI as the stable backend and keep the OpenCode skill as a query workflow that reads the generated knowledge base and calls the CLI when needed.

This separates responsibilities:

- The CLI owns crawling, conversion, indexing, updates, and search.
- The Markdown repository owns durable source and wiki artifacts.
- The OpenCode skill owns agent behavior during programming tasks.

## Non-Goals For The First Version

- Full browser rendering for JavaScript-heavy sites.
- Vector database or embedding-based RAG.
- Fully automated LLM synthesis of topic pages.
- Crawling arbitrary websites without domain/path restrictions.
- Publishing or hosting the generated documentation.

## Project Layout

```text
docs-claw/
  pyproject.toml
  src/docs_claw/
    __init__.py
    cli.py
    registry.py
    crawler.py
    converter.py
    wiki.py
    search.py
    adapters/
      __init__.py
      sphinx.py
  sources/
    <source-id>/source.yml
  raw/
    <source-id>/pages/*.html
    <source-id>/manifest.json
  docs/
    <source-id>/pages/*.md
  wiki/
    <source-id>/index.md
    <source-id>/overview.md
    <source-id>/log.md
    <source-id>/topics/*.md
  skills/
    official-docs/SKILL.md
  tests/
```

## Components

### Source Registry

The registry stores one `source.yml` per documentation source under `sources/<source-id>/source.yml`.

Each source includes:

- `id`: stable source id, such as `ryzenai`.
- `url`: start URL.
- `type`: initially `sphinx`.
- `allowed_domains`: domains that may be crawled.
- `allowed_path_prefixes`: path prefixes that may be crawled.
- `created_at` and `updated_at` timestamps.

The registry prevents accidental broad crawling and gives the update command enough metadata to refresh a source without repeating arguments.

### Sphinx Crawler

The crawler starts from the configured URL, fetches HTML, extracts same-site documentation links, normalizes URLs, filters them by allowed domain and path prefix, and stores each page under `raw/<source-id>/pages/`.

It writes `raw/<source-id>/manifest.json` with URL, local path, title, content hash, status code, and fetch timestamp. The manifest is the basis for incremental updates and change detection.

The first version uses static HTML fetching with `httpx` and `BeautifulSoup`. It does not execute JavaScript.

### Markdown Converter

The converter reads raw HTML pages, extracts the main documentation content, removes navigation and boilerplate, converts the content to Markdown, and writes `docs/<source-id>/pages/*.md`.

Each page includes YAML frontmatter:

```yaml
---
source_id: ryzenai
source_url: https://example.com/page.html
title: Page Title
fetched_at: "2026-05-23T00:00:00Z"
content_hash: abc123
site_type: sphinx
---
```

The converter preserves headings, code blocks, tables where possible, links, and image references.

### Wiki Builder

The wiki builder creates a persistent Markdown knowledge base from converted pages.

It writes:

- `wiki/<source-id>/index.md`: page catalog grouped by section.
- `wiki/<source-id>/overview.md`: source overview, update metadata, and prominent pages.
- `wiki/<source-id>/topics/*.md`: deterministic topic pages based on headings and page titles.
- `wiki/<source-id>/log.md`: append-only operational history.

The first version uses deterministic extraction rather than LLM synthesis. This keeps the implementation testable and avoids depending on an external model. Later versions can add an optional LLM summarizer that updates topic pages with richer synthesis.

### Search

The search command scans generated Markdown files and ranks matches using simple lexical scoring across title, headings, body text, and URL. It returns source file paths and source URLs so an agent can inspect relevant pages.

This is enough for a first local skill backend. The design leaves room for replacing search with BM25, SQLite FTS, or qmd later.

### OpenCode Skill

The `official-docs` skill teaches OpenCode how to use the generated knowledge base while programming.

The skill workflow is:

1. Inspect `wiki/*/index.md` to find available documentation sources.
2. Use `docs-claw search <source-id> <query>` when a source is known.
3. Read relevant `wiki/`, `docs/`, or topic Markdown files.
4. Answer with source URLs and local file references.
5. If the source is stale or missing, suggest or run `docs-claw update <source-id>` when appropriate.

The skill should not contain crawler logic. It should rely on the CLI.

## CLI

The CLI exposes these commands:

```bash
docs-claw add <source-id> <url> --type sphinx
docs-claw crawl <source-id>
docs-claw convert <source-id>
docs-claw build-wiki <source-id>
docs-claw update <source-id>
docs-claw search <source-id> "<query>"
docs-claw status
```

`update` runs `crawl`, `convert`, and `build-wiki` in sequence. This is the manual one-command refresh mechanism.

## Data Flow

```text
source.yml
  -> crawl official site
  -> raw HTML + manifest
  -> convert to Markdown pages
  -> build wiki index, overview, topics, log
  -> OpenCode skill searches and reads wiki during programming
```

## Error Handling

- Network failures are reported with the failing URL and do not delete existing artifacts.
- Pages outside allowed domains or prefixes are skipped.
- Empty conversions are skipped and reported.
- Unknown source ids produce a clear registry error.
- Unsupported site types produce a clear adapter error.
- Updates write files deterministically and preserve previous successful artifacts when a fetch fails before conversion.

## Testing

Unit tests cover:

- Registry creation and loading.
- URL normalization and scope filtering.
- Sphinx link extraction.
- HTML main-content extraction.
- Markdown frontmatter generation.
- Search ranking.

Integration tests use fixture HTML pages to verify:

- `add -> update -> search` works end to end.
- Only scoped links are crawled.
- Wiki files are generated.

## Success Criteria

- A user can register the Ryzen AI documentation URL with one command.
- A user can run one update command to crawl, convert, and build the local wiki.
- Generated Markdown pages include source URLs and useful titles.
- The generated wiki includes an index, overview, topics directory, and log.
- The OpenCode skill can guide an agent to answer programming questions using the local official docs.
- Tests pass without requiring network access.
