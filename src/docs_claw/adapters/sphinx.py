from __future__ import annotations

from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from docs_claw.registry import SourceConfig


MAIN_SELECTORS = [
    "article.bd-article",
    "div.document",
    "div.body",
    "main",
    "article",
    "div[role='main']",
]


def normalize_url(base_url: str, href: str) -> str:
    absolute = urljoin(base_url, href)
    normalized, _fragment = urldefrag(absolute)
    return normalized


def is_allowed_url(source: SourceConfig, url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in source.allowed_domains:
        return False
    return any(parsed.path.startswith(prefix) for prefix in source.allowed_path_prefixes)


def extract_links(source: SourceConfig, base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        if anchor["href"].startswith("#"):
            continue
        url = normalize_url(base_url, anchor["href"])
        parsed = urlparse(url)
        if parsed.path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf")):
            continue
        if is_allowed_url(source, url) and url not in seen:
            seen.add(url)
            links.append(url)
    return links


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)
    title = soup.find("title")
    if title and title.get_text(strip=True):
        return title.get_text(" ", strip=True)
    return "Untitled"


def extract_main_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in MAIN_SELECTORS:
        node = soup.select_one(selector)
        if node:
            for unwanted in node.select("script, style, nav, footer"):
                unwanted.decompose()
            return str(node)
    body = soup.find("body")
    return str(body or soup)
