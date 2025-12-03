# src/tools/mcp/wikipedia_mcp.py

from typing import List, Dict, Any
import httpx

WIKI_API_ENDPOINT = "https://en.wikipedia.org/w/api.php"


async def search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Perform a simple Wikipedia search.

    Returns a list of dicts: [{title, description, url}, ...]
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(WIKI_API_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()

    search_results = data.get("query", {}).get("search", []) or []

    results: List[Dict[str, Any]] = []
    for item in search_results[:limit]:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        results.append(
            {
                "title": title,
                "description": snippet,
                "url": url,
            }
        )

    return results
