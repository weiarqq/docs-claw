# Tree Navigation Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a multi-turn tree navigation protocol that renders bounded tree views from `tree.json`, forces selection down to leaf nodes before returning text, and splits large trees into independent roots.

**Architecture:** Upgrade `tree.json` to a versioned envelope with `config` and `roots`, while keeping a compatibility loader for old single-root JSON. Add `tree_navigation.py` for view rendering, leaf resolving, stats, pagination, and root splitting helpers; keep `tree_wiki.py` responsible for building tree data. Expose the protocol through `tree-view`, `tree-resolve`, and `tree-stats` CLI commands and update the OpenCode skill to use those commands instead of loading full `tree.json` into context.

**Tech Stack:** Python standard library, argparse, JSON, pathlib, pytest.

---

## File Structure

- Modify `src/docs_claw/tree_wiki.py`: write v2 tree envelope, config, roots, max root split.
- Create `src/docs_claw/tree_navigation.py`: load tree, render bounded views, resolve leaves, compute stats.
- Modify `src/docs_claw/cli.py`: add `tree-view`, `tree-resolve`, `tree-stats`, `--max-view-nodes`, `--max-root-nodes`.
- Modify `tests/test_tree_wiki.py`: v2 envelope and max-root split tests.
- Create `tests/test_tree_navigation.py`: view, pagination, leaf-only resolve, and stats tests.
- Modify `tests/test_cli.py`: CLI protocol tests.
- Modify `skills/official-docs/SKILL.md` and `src/docs_claw/skills/official-docs/SKILL.md`: multi-turn selection protocol.
- Modify `README.md`: document protocol and configurable limits.

## Tasks

### Task 1: Tree JSON V2 Envelope

- [ ] Write a test asserting `tree.json` has `version`, `config.max_view_nodes`, `config.max_root_nodes`, and `roots`.
- [ ] Update `build_tree_wiki()` signature to accept `max_view_nodes=100` and `max_root_nodes=500`.
- [ ] Write v2 envelope while preserving node structure under `roots[0]`.
- [ ] Run `uv run --extra dev pytest tests/test_tree_wiki.py -v`.

### Task 2: Tree View Rendering

- [ ] Create `tests/test_tree_navigation.py` with a fixture v2 tree.
- [ ] Test `render_tree_view(root, source_id, root_node_id="root", limit=100, offset=0)` outputs root and first/second-level children in the requested format.
- [ ] Test pagination shows `Showing N of M selectable nodes` and an offset hint.
- [ ] Implement `load_tree()`, `find_node()`, `flatten_selectable_nodes()`, and `render_tree_view()`.
- [ ] Run `uv run --extra dev pytest tests/test_tree_navigation.py -v`.

### Task 3: Leaf Resolve

- [ ] Test resolving a leaf returns source URL, file, line+limit, and text snippet.
- [ ] Test resolving a non-leaf returns an error requiring another `tree-view` selection.
- [ ] Implement `TreeResolveError` and `resolve_leaf_text()`.
- [ ] Run `uv run --extra dev pytest tests/test_tree_navigation.py -v`.

### Task 4: Root Split And Stats

- [ ] Add test building more nodes than `max_root_nodes` and assert multiple independent roots are written.
- [ ] Add stats test showing root count and node counts.
- [ ] Implement broad root chunking by top-level nodes and `tree_stats()`.
- [ ] Run tree wiki and navigation tests.

### Task 5: CLI And Docs

- [ ] Add `tree-view`, `tree-resolve`, and `tree-stats` commands.
- [ ] Add `--max-view-nodes` and `--max-root-nodes` to `build-tree` and update tree options.
- [ ] Update OpenCode skill to require `tree-view -> select -> tree-view -> select leaf -> tree-resolve`.
- [ ] Update README with examples and configurable limits.
- [ ] Run full verification.

## Self-Review

- Spec coverage: multi-turn selection, bounded views, configurable 100 limit, configurable 500 root split, independent roots, and leaf-only resolving are covered.
- Placeholder scan: no placeholders remain.
- Type consistency: `render_tree_view`, `resolve_leaf_text`, `tree_stats`, `max_view_nodes`, and `max_root_nodes` are used consistently.
