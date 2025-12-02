import os
import httpx
from typing import List, Dict, Any

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


async def google_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Google Custom Search tool.

    Args:
        query: Search query.
        limit: Max number of results (max 10 per API spec).

    Returns:
        List of dicts with: title, description, url.
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        raise RuntimeError(
            "Missing GOOGLE_SEARCH_API_KEY or GOOGLE_SEARCH_CX. "
            "Add them to your .env."
        )

    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_CX,
        "q": query,
        "num": limit,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(GOOGLE_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results: List[Dict[str, Any]] = []
    for item in data.get("items", []):
        results.append(
            {
                "title": item.get("title"),
                "description": item.get("snippet"),
                "url": item.get("link"),
            }
        )
    return results
