from typing import Dict, Any, List

from src.prompts.system_instructions import ORACLE_BASE
from src.tools import TOOL_REGISTRY


TIME_SENSITIVE_KEYWORDS = [
    "today",
    "yesterday",
    "this week",
    "this month",
    "this year",
    "latest",
    "recent",
    "news",
    "update",
    "stock",
    "price",
    "election",
    "covid",
    "war",
    "conflict",
    "market",
    "rate",
    "interest rate",
    "inflation",
    "weather",
]


def is_time_sensitive_query(text: str) -> bool:
    lower = text.lower()
    if any(kw in lower for kw in TIME_SENSITIVE_KEYWORDS):
        return True

    # Rough heuristic: mentions a very recent year explicitly
    for year in range(2023, 2031):
        if str(year) in lower:
            return True

    return False


class OracleAgent:
    """
    Oracle agent.

    - Handles knowledge / information questions.
    - Uses Wikipedia for stable background info.
    - Uses Google Search for time-sensitive / newsy queries.
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    async def handle(self, user_message: str, context_text: str) -> Dict[str, Any]:
        use_google = is_time_sensitive_query(user_message)

        # Decide which tool to call
        tool_name = "search.google" if use_google else "search.wikipedia"
        search_fn = TOOL_REGISTRY.get(tool_name)

        search_results: List[Dict[str, Any]] = []

        if search_fn is not None:
            try:
                search_results = await search_fn(user_message, limit=3)  # type: ignore[arg-type]
            except Exception as e:
                # Fail softly; still try to answer with context only
                search_results = [
                    {
                        "title": "Search error",
                        "description": str(e),
                        "url": "",
                    }
                ]
        else:
            search_results = []

        # If Google was chosen but returned nothing, try Wikipedia as fallback
        if use_google and not search_results:
            alt_fn = TOOL_REGISTRY.get("search.wikipedia")
            if alt_fn is not None:
                try:
                    search_results = await alt_fn(user_message, limit=3)  # type: ignore[arg-type]
                    tool_name = "search.wikipedia"
                except Exception:
                    pass

        # Format search results for the prompt
        if search_results:
            snippets = []
            for r in search_results:
                snippets.append(
                    f"- {r.get('title', '')}: {r.get('description', '')} ({r.get('url', '')})"
                )
            search_block = f"SEARCH TOOL ({tool_name}) RESULTS:\n" + "\n".join(snippets)
        else:
            search_block = f"SEARCH TOOL ({tool_name}) RESULTS: (none or unavailable)"

        prompt = f"""
{ORACLE_BASE}

Context from memory:
{context_text}

{search_block}

User question:
{user_message}

Using the information above:
- Answer briefly and clearly.
- If the search results conflict or seem incomplete, mention uncertainty.
- If you are still unsure, say you are unsure rather than guessing.
""".strip()

        answer = await self.llm.generate(prompt)
        return {
            "answer": answer,
            "search_results": search_results,
            "tool_used": tool_name,
        }
