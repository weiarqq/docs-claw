from __future__ import annotations

import argparse
from pathlib import Path

from docs_claw.converter import convert_source
from docs_claw.crawler import crawl_source
from docs_claw.paths import repo_root
from docs_claw.registry import add_source, list_sources, load_source
from docs_claw.search import search_source
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

    search = subparsers.add_parser("search", help="Search generated docs")
    search.add_argument("source_id")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)

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

    if args.command == "search":
        results = search_source(root, args.source_id, args.query, args.limit)
        for result in results:
            print(f"{result.score}\t{result.title}\t{result.path.relative_to(root)}")
            if result.source_url:
                print(f"  source: {result.source_url}")
            if result.snippet:
                print(f"  {result.snippet}")
        return 0

    source = load_source(root, args.source_id)
    if args.command == "crawl":
        result = crawl_source(root, source)
        print(f"Crawled {result.pages_crawled} pages")
        return 0
    if args.command == "convert":
        result = convert_source(root, source)
        print(f"Converted {result.pages_converted} pages, skipped {result.pages_skipped}")
        return 0
    if args.command == "build-wiki":
        result = build_wiki(root, source)
        print(f"Indexed {result.pages_indexed} pages, wrote {result.topics_written} topics")
        return 0
    if args.command == "update":
        crawl = crawl_source(root, source)
        convert = convert_source(root, source)
        wiki = build_wiki(root, source)
        print(
            f"Updated {source.id}: crawled {crawl.pages_crawled}, "
            f"converted {convert.pages_converted}, indexed {wiki.pages_indexed}"
        )
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
