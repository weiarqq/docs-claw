# Official Docs Claw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI and OpenCode skill that crawl official docs, convert them to Markdown, maintain an llm-wiki-style knowledge base, support one-command updates, and answer programming questions from the local official docs.

**Architecture:** The CLI is the backend for registry, crawling, conversion, wiki generation, and search. Generated artifacts live in `sources/`, `raw/`, `docs/`, and `wiki/`. The OpenCode skill reads the wiki and calls the CLI instead of embedding crawler logic.

**Tech Stack:** Python 3.11+, `httpx`, `beautifulsoup4`, `markdownify`, `PyYAML`, `pytest`, standard-library `argparse`.

---

## File Structure

- Create `pyproject.toml`: package metadata, console script, dependencies, pytest config.
- Create `src/docs_claw/__init__.py`: package version.
- Create `src/docs_claw/paths.py`: repository-relative path helpers.
- Create `src/docs_claw/registry.py`: source config creation/loading/status.
- Create `src/docs_claw/adapters/sphinx.py`: Sphinx URL normalization, scoping, link extraction, title/content extraction.
- Create `src/docs_claw/crawler.py`: crawl pages and write raw HTML manifest.
- Create `src/docs_claw/converter.py`: convert raw HTML to Markdown pages with frontmatter.
- Create `src/docs_claw/wiki.py`: build index, overview, topic pages, and log.
- Create `src/docs_claw/search.py`: lexical search over generated Markdown.
- Create `src/docs_claw/cli.py`: command-line interface.
- Create `skills/official-docs/SKILL.md`: OpenCode skill workflow.
- Create tests under `tests/` for registry, Sphinx adapter, conversion, wiki generation, search, and CLI integration.

## Tasks

### Task 1: Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/docs_claw/__init__.py`
- Create: `src/docs_claw/paths.py`
- Create: `tests/test_paths.py`

- [ ] Add package metadata, dependencies, and console script in `pyproject.toml`.
- [ ] Add `__version__` in `src/docs_claw/__init__.py`.
- [ ] Add `repo_root()`, `ensure_dir()`, and `safe_id()` helpers in `src/docs_claw/paths.py`.
- [ ] Add tests for `safe_id()` accepting lowercase ids and rejecting path traversal.
- [ ] Run `python -m pytest tests/test_paths.py -v` and expect all tests to pass.

### Task 2: Source Registry

**Files:**
- Create: `src/docs_claw/registry.py`
- Create: `tests/test_registry.py`

- [ ] Write tests for creating a source config from `ryzenai` and `https://ryzenai.docs.amd.com/en/latest/index.html`.
- [ ] Implement `SourceConfig` dataclass.
- [ ] Implement `add_source(root, source_id, url, site_type)`.
- [ ] Implement `load_source(root, source_id)`.
- [ ] Implement `list_sources(root)`.
- [ ] Run `python -m pytest tests/test_registry.py -v` and expect all tests to pass.

### Task 3: Sphinx Adapter

**Files:**
- Create: `src/docs_claw/adapters/__init__.py`
- Create: `src/docs_claw/adapters/sphinx.py`
- Create: `tests/test_sphinx_adapter.py`

- [ ] Write tests for URL normalization, allowed scope filtering, title extraction, content extraction, and link extraction.
- [ ] Implement `normalize_url()` to drop fragments and normalize relative links.
- [ ] Implement `is_allowed_url()` based on domains and path prefixes.
- [ ] Implement `extract_links()` from anchor tags.
- [ ] Implement `extract_title()` and `extract_main_content()` with Sphinx-friendly selectors.
- [ ] Run `python -m pytest tests/test_sphinx_adapter.py -v` and expect all tests to pass.

### Task 4: Crawler

**Files:**
- Create: `src/docs_claw/crawler.py`
- Create: `tests/test_crawler.py`

- [ ] Write tests using a fake fetcher that returns three linked HTML pages and one out-of-scope link.
- [ ] Implement `CrawlPage` dataclass.
- [ ] Implement `crawl_source(root, source, fetcher=None, max_pages=500)`.
- [ ] Store raw HTML files under `raw/<source-id>/pages/` using hashed filenames.
- [ ] Store `raw/<source-id>/manifest.json` with URL, path, title, hash, fetched time, status.
- [ ] Run `python -m pytest tests/test_crawler.py -v` and expect all tests to pass.

### Task 5: Markdown Converter

**Files:**
- Create: `src/docs_claw/converter.py`
- Create: `tests/test_converter.py`

- [ ] Write tests that convert fixture HTML manifest entries into Markdown with YAML frontmatter.
- [ ] Implement `convert_source(root, source)`.
- [ ] Use `markdownify` to convert extracted main content.
- [ ] Preserve source URL, title, fetched timestamp, content hash, and site type in frontmatter.
- [ ] Skip empty converted pages and report skipped count.
- [ ] Run `python -m pytest tests/test_converter.py -v` and expect all tests to pass.

### Task 6: Wiki Builder

**Files:**
- Create: `src/docs_claw/wiki.py`
- Create: `tests/test_wiki.py`

- [ ] Write tests that build wiki files from two converted Markdown pages.
- [ ] Implement frontmatter parsing for title and source URL.
- [ ] Implement `build_wiki(root, source)`.
- [ ] Generate `wiki/<source-id>/index.md` with page links and source URLs.
- [ ] Generate `wiki/<source-id>/overview.md` with source metadata and page count.
- [ ] Generate deterministic topic pages under `wiki/<source-id>/topics/` from page headings.
- [ ] Append an update entry to `wiki/<source-id>/log.md`.
- [ ] Run `python -m pytest tests/test_wiki.py -v` and expect all tests to pass.

### Task 7: Search

**Files:**
- Create: `src/docs_claw/search.py`
- Create: `tests/test_search.py`

- [ ] Write tests that search generated wiki and docs Markdown for `quantization`.
- [ ] Implement `search_source(root, source_id, query, limit=10)`.
- [ ] Rank results by occurrences in title, headings, body, and source URL.
- [ ] Return local path, title, source URL, score, and snippet.
- [ ] Run `python -m pytest tests/test_search.py -v` and expect all tests to pass.

### Task 8: CLI

**Files:**
- Create: `src/docs_claw/cli.py`
- Create: `tests/test_cli.py`

- [ ] Write CLI tests for `add`, `status`, and `search` using temporary repo roots.
- [ ] Implement `docs-claw add <source-id> <url> --type sphinx`.
- [ ] Implement `docs-claw crawl <source-id>`.
- [ ] Implement `docs-claw convert <source-id>`.
- [ ] Implement `docs-claw build-wiki <source-id>`.
- [ ] Implement `docs-claw update <source-id>` as crawl, convert, and build-wiki.
- [ ] Implement `docs-claw search <source-id> <query>`.
- [ ] Implement `docs-claw status`.
- [ ] Run `python -m pytest tests/test_cli.py -v` and expect all tests to pass.

### Task 9: OpenCode Skill

**Files:**
- Create: `skills/official-docs/SKILL.md`
- Create: `tests/test_skill_file.py`

- [ ] Write a test that verifies the skill file references `docs-claw search`, `docs-claw update`, `wiki/`, and source URLs.
- [ ] Write the skill instructions for querying official docs during programming.
- [ ] Run `python -m pytest tests/test_skill_file.py -v` and expect all tests to pass.

### Task 10: End-To-End Verification

**Files:**
- Modify: `READE.md`
- Create: `tests/test_end_to_end.py`

- [ ] Add an offline end-to-end test for `add -> crawl -> convert -> build-wiki -> search` using a fake fetcher.
- [ ] Document install and usage in `READE.md`.
- [ ] Run `python -m pytest -v` and expect all tests to pass.
- [ ] Run `python -m docs_claw.cli --help` and expect command help output.

## Self-Review

- Spec coverage: registry, crawler, converter, wiki, search, one-command update, and skill are covered.
- Placeholder scan: no placeholders remain.
- Type consistency: `SourceConfig`, `crawl_source`, `convert_source`, `build_wiki`, and `search_source` names are consistent across tasks.
