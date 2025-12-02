from typing import List, Dict, Any
import httpx

WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/rest.php/v1/search/title"


async def wikipedia_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Simple Wikipedia search tool.

    Args:
        query: Search query.
        limit: Max number of results.

    Returns:
        List of dicts with: title, description, url.
    """
    params = {"q": query, "limit": limit}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(WIKIPEDIA_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results: List[Dict[str, Any]] = []
    for page in data.get("pages", []):
        title = page.get("title", "")
        excerpt = page.get("excerpt", "")
        key = page.get("key", "")
        url = f"https://en.wikipedia.org/wiki/{key}" if key else ""

        results.append(
            {
                "title": title,
                "description": excerpt,
                "url": url,
            }
        )

    return results
