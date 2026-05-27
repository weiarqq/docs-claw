from __future__ import annotations

import argparse
from pathlib import Path

from docs_claw.converter import convert_source
from docs_claw.crawler import FetchError, crawl_source
from docs_claw.opencode import init_opencode
from docs_claw.paths import repo_root
from docs_claw.registry import add_source, list_sources, load_source
from docs_claw.search import search_source
from docs_claw.tree_wiki import build_tree_wiki
from docs_claw.tree_navigation import TreeResolveError, render_tree_view, resolve_leaf_text, tree_stats
from docs_claw.wiki import build_wiki


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docs-claw")
    parser.add_argument("--root", type=Path, default=None, help="Repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Register a documentation source")
    add.add_argument("source_id")
    add.add_argument("url")
    add.add_argument("--type", default="sphinx", choices=["sphinx"])

    for name in ["crawl", "convert", "build-wiki", "update"]:
        command = subparsers.add_parser(name)
        command.add_argument("source_id")
        if name in {"crawl", "update"}:
            command.add_argument(
                "--ignore-proxy",
                action="store_true",
                help="Ignore HTTP_PROXY, HTTPS_PROXY, and ALL_PROXY environment variables",
            )
        if name == "update":
            command.add_argument("--tree-name", default=None, help="Also build tree wiki with this root name")
            command.add_argument("--tree-description", default=None, help="Root description for --tree-name")
            command.add_argument("--max-view-nodes", type=int, default=100, help="Default tree-view page size")
            command.add_argument("--max-root-nodes", type=int, default=500, help="Maximum nodes per independent root")

    build_tree = subparsers.add_parser("build-tree", help="Build a multi-way tree wiki")
    build_tree.add_argument("source_id")
    build_tree.add_argument("--name", required=True, help="Root knowledge-base name")
    build_tree.add_argument("--description", default=None, help="Root description, <= 100 characters recommended")
    build_tree.add_argument("--max-view-nodes", type=int, default=100, help="Default tree-view page size")
    build_tree.add_argument("--max-root-nodes", type=int, default=500, help="Maximum nodes per independent root")

    tree_view = subparsers.add_parser("tree-view", help="Render a bounded tree view for multi-turn selection")
    tree_view.add_argument("source_id")
    tree_view.add_argument("--root-node", default="root", help="Node id to render from")
    tree_view.add_argument("--limit", type=int, default=None, help="Maximum selectable nodes to show")
    tree_view.add_argument("--offset", type=int, default=0, help="Selectable node offset")

    tree_resolve = subparsers.add_parser("tree-resolve", help="Resolve a selected leaf node to source text")
    tree_resolve.add_argument("source_id")
    tree_resolve.add_argument("node_id")

    tree_stats_parser = subparsers.add_parser("tree-stats", help="Show tree root and node counts")
    tree_stats_parser.add_argument("source_id")

    search = subparsers.add_parser("search", help="Search generated docs")
    search.add_argument("source_id")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)

    init = subparsers.add_parser("init-opencode", help="Install the OpenCode skill")
    init.add_argument("--home", type=Path, default=None, help="Home directory to install into")
    init.add_argument("--kb-root", type=Path, default=None, help="Shared docs knowledge-base root")
    init.add_argument("--force", action="store_true", default=True, help="Overwrite existing skill file")
    init.add_argument("--no-force", action="store_false", dest="force", help="Do not overwrite existing skill file")

    subparsers.add_parser("status", help="List registered sources")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else repo_root()

    if args.command == "add":
        source = add_source(root, args.source_id, args.url, args.type)
        print(f"Added source {source.id}: {source.url}")
        return 0

    if args.command == "status":
        sources = list_sources(root)
        if not sources:
            print("No sources registered")
            return 0
        for source in sources:
            print(f"{source.id}\t{source.type}\t{source.url}\tupdated={source.updated_at}")
        return 0

    if args.command == "init-opencode":
        result = init_opencode(home=args.home, kb_root=args.kb_root, force=args.force)
        action = "Installed" if result.skill_installed else "Kept existing"
        print(f"{action} OpenCode skill: {result.skill_path}")
        print(f"Knowledge-base root: {result.kb_root}")
        print("Restart OpenCode so it reloads skills.")
        print("Example: docs-claw --root ~/docs-claw-kb add ryzenai https://ryzenai.docs.amd.com/en/latest/index.html --type sphinx")
        return 0

    if args.command == "search":
        results = search_source(root, args.source_id, args.query, args.limit)
        for result in results:
            print(f"{result.score}\t{result.title}\t{result.path.relative_to(root)}")
            if result.source_url:
                print(f"  source: {result.source_url}")
            if result.snippet:
                print(f"  {result.snippet}")
        return 0

    if args.command == "tree-view":
        print(render_tree_view(root, args.source_id, root_node_id=args.root_node, limit=args.limit, offset=args.offset), end="")
        return 0

    if args.command == "tree-resolve":
        try:
            print(resolve_leaf_text(root, args.source_id, args.node_id), end="")
        except TreeResolveError as error:
            print(str(error))
            return 1
        return 0

    if args.command == "tree-stats":
        print(tree_stats(root, args.source_id), end="")
        return 0

    source = load_source(root, args.source_id)
    if args.command == "crawl":
        result = crawl_source(root, source, ignore_proxy=args.ignore_proxy)
        print(f"Crawled {result.pages_crawled} pages, failed {result.pages_failed} pages")
        return 0
    if args.command == "convert":
        result = convert_source(root, source)
        print(f"Converted {result.pages_converted} pages, skipped {result.pages_skipped}")
        return 0
    if args.command == "build-wiki":
        result = build_wiki(root, source)
        print(f"Indexed {result.pages_indexed} pages, wrote {result.topics_written} topics")
        return 0
    if args.command == "build-tree":
        result = build_tree_wiki(
            root,
            source,
            name=args.name,
            description=args.description,
            max_view_nodes=args.max_view_nodes,
            max_root_nodes=args.max_root_nodes,
        )
        print(
            f"Built tree wiki: {result.tree_path.relative_to(root)} "
            f"({result.nodes_written} nodes, {result.references_indexed} references)"
        )
        return 0
    if args.command == "update":
        try:
            crawl = crawl_source(root, source, ignore_proxy=args.ignore_proxy)
        except FetchError as error:
            _print_fetch_error(error)
            return 1
        convert = convert_source(root, source)
        wiki = build_wiki(root, source)
        tree = None
        if args.tree_name:
            tree = build_tree_wiki(
                root,
                source,
                name=args.tree_name,
                description=args.tree_description,
                max_view_nodes=args.max_view_nodes,
                max_root_nodes=args.max_root_nodes,
            )
        tree_summary = f", tree nodes {tree.nodes_written}" if tree else ""
        print(
            f"Updated {source.id}: crawled {crawl.pages_crawled}, "
            f"failed {crawl.pages_failed}, converted {convert.pages_converted}, "
            f"indexed {wiki.pages_indexed}{tree_summary}"
        )
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


def _print_fetch_error(error: FetchError) -> None:
    print(f"Failed to fetch {error.url}")
    print("")
    print("Reason:")
    print(error)
    print("")
    print("If this happens while using a proxy, try:")
    print("  docs-claw --root <kb-root> update <source-id> --ignore-proxy")
    print("")
    print("Also check:")
    print("  env | grep -i proxy")
    print(f"  curl -I {error.url}")
