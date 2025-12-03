# src/tools/mcp/google_search_mcp.py

import os
from typing import List, Dict, Any

import httpx

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

# How many characters of page text to keep per result
MAX_PAGE_TEXT_CHARS = 2000


async def _fetch_page_text(url: str) -> str:
    """
    Fetch the raw HTML of a page and extract a very rough text version.

    This is intentionally simple to avoid extra dependencies.
    For a production system you'd likely use BeautifulSoup, trafilatura, etc.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text
    except Exception:
        return ""

    # Very crude stripping of tags.
    # You can swap this for BeautifulSoup if you want nicer text.
    import re

    # Remove script/style
    html = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > MAX_PAGE_TEXT_CHARS:
        text = text[:MAX_PAGE_TEXT_CHARS] + "..."

    return text


async def search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Perform a Google Custom Search and return enriched results.

    Each result dict includes:
    - title
    - description (Google snippet)
    - url
    - display_link (domain)
    - page_text (crude extracted main text from the target page)
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        raise RuntimeError(
            "Missing GOOGLE_SEARCH_API_KEY or GOOGLE_SEARCH_CX in environment"
        )

    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_CX,
        "q": query,
        "num": limit,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(SEARCH_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items", []) or []

    results: List[Dict[str, Any]] = []
    for item in items[:limit]:
        url = item.get("link")
        page_text = await _fetch_page_text(url) if url else ""

        results.append(
            {
                "title": item.get("title"),
                "description": item.get("snippet"),
                "url": url,
                "display_link": item.get("displayLink"),
                "page_text": page_text,
            }
        )

    return results
