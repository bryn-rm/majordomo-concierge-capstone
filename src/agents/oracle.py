# src/agents/oracle.py

from typing import Dict, Any, List
import re

from src.prompts.system_instructions import ORACLE_BASE
from src.tools import TOOL_REGISTRY

# --------------------------------------------------------------------
# Heuristics for deciding when to use live Google search vs Wikipedia
# --------------------------------------------------------------------

# Generic time-sensitive language
TIME_SENSITIVE_KEYWORDS = [
    "today",
    "yesterday",
    "this week",
    "this weekend",
    "this month",
    "this year",
    "latest",
    "recent",
    "recently",
    "right now",
    "currently",
    "breaking",
    "news",
    "update",
]

# Domains that are almost always time-sensitive when asked about
DOMAIN_KEYWORDS = [
    "stock",
    "share price",
    "price",
    "market",
    "rate",
    "interest rate",
    "inflation",
    "weather",
    "forecast",
    "election",
    "covid",
    "war",
    "conflict",
]

# Sports result / score style questions
SPORTS_RESULT_KEYWORDS = [
    "score",
    "final score",
    "winning margin",
    "won by",
    "who won",
    "what was the score",
    "result of the match",
    "result of the game",
    "full-time score",
    "ft score",
    "match result",
    "game result",
]

# Patterns for explicit recent years (adjust as you like)
RECENT_YEAR_PATTERN = re.compile(r"\b(20[1-4]\d|2024|2025)\b")


def is_time_sensitive_query(text: str) -> bool:
    """
    Heuristic classifier: decide whether a query should go to live search
    (Google Custom Search) rather than just Wikipedia / model knowledge.

    We treat as time-sensitive if:
    - It mentions relative / recency phrases ("last week", "latest", etc.), OR
    - It mentions obviously time-varying domains (stocks, rates, weather, etc.), OR
    - It looks like a sports result / score question, OR
    - It contains an explicit recent year.
    """
    lower = text.lower()

    # Explicit relative-time phrases
    relative_phrases = [
        "last week",
        "last weekend",
        "last month",
        "last year",
        "this week",
        "this month",
        "this year",
        "tonight",
        "this evening",
        "this morning",
        "earlier today",
    ]

    if any(kw in lower for kw in TIME_SENSITIVE_KEYWORDS):
        return True

    if any(kw in lower for kw in relative_phrases):
        return True

    if any(kw in lower for kw in DOMAIN_KEYWORDS):
        return True

    if any(kw in lower for kw in SPORTS_RESULT_KEYWORDS):
        return True

    if RECENT_YEAR_PATTERN.search(lower):
        return True

    return False


def _is_sports_result_query(text: str) -> bool:
    lower = text.lower()
    if any(kw in lower for kw in SPORTS_RESULT_KEYWORDS):
        return True
    # very rough sports-ish heuristic
    if "vs" in lower or "v " in lower:
        if "rugby" in lower or "football" in lower or "match" in lower or "game" in lower:
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
        """
        Main entrypoint for the Oracle.

        - Decide whether the question is time-sensitive.
        - For sports-style result queries, augment the search query with "final score result".
        - Call the appropriate search tool via TOOL_REGISTRY:
            * 'search.google'     -> Google Custom Search MCP
            * 'search.wikipedia'  -> Wikipedia MCP
        - Optionally fall back from Google to Wikipedia if Google returns nothing.
        - Ask the LLM to synthesise a clear answer from search + context.
        """
        use_google = is_time_sensitive_query(user_message)
        lower = user_message.lower()

        # Decide which base tool to call
        tool_name = "search.google" if use_google else "search.wikipedia"
        search_fn = TOOL_REGISTRY.get(tool_name)

        # Build the query we'll actually send to the search tool
        query_for_search = user_message
        if _is_sports_result_query(user_message):
            # Nudge the search engine harder toward a result/score page
            query_for_search = f"{user_message} final score result"

        search_results: List[Dict[str, Any]] = []

        if search_fn is not None:
            try:
                # MCP wrappers expected signature:
                #   async def search(query: str, limit: int = 3) -> List[Dict[str, Any]]
                search_results = await search_fn(query_for_search, limit=5)  # type: ignore[arg-type]
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
            # Tool not registered; we can still answer from memory/context
            search_results = []

        # If Google was chosen but returned nothing, try Wikipedia as fallback
        if use_google and not search_results:
            alt_fn = TOOL_REGISTRY.get("search.wikipedia")
            if alt_fn is not None:
                try:
                    search_results = await alt_fn(user_message, limit=5)  # type: ignore[arg-type]
                    tool_name = "search.wikipedia"
                except Exception:
                    # Ignore fallback errors; we'll just answer with what we have
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

        # Build a strong prompt that pushes the model to squeeze everything it can
        prompt = f"""
{ORACLE_BASE}

You are a retrieval + reasoning specialist. You are given:

1) Context from the user's long-term memory (may be empty).
2) A block of search results from external tools (Google or Wikipedia).

Your job:
- Extract as much concrete, factual information as possible from the search results.
- For sports / score / result queries, try very hard to identify the likely final score or clear outcome.
- Only say you are "unsure" if the search results truly contain no relevant information at all.

Context from memory:
{context_text}

{search_block}

User question:
{user_message}

Using ONLY the information above:
- Give a direct answer to the user if you can.
- If several results hint at the same answer, you may infer the most likely one (and you can mention uncertainty).
- If the search results discuss the match/event but do not explicitly state the score/result, summarise what *is* known instead of just saying "unsure".
- If you genuinely cannot answer from the results, say that you are unsure and suggest where the user might check next.
""".strip()

        answer = await self.llm.generate(prompt)
        return {
            "answer": answer,
            "search_results": search_results,
            "tool_used": tool_name,
        }
