# src/agents/archivist.py

from typing import Dict, Any, List

from src.tools import TOOL_REGISTRY
from src.prompts.system_instructions import SCRIBE_BASE


class ArchivistAgent:
    """
    Archivist / Memory Insight agent.

    Called by Scribe when the user asks meta-questions about their history, e.g.:
      - "What have I been saying about work?"
      - "Have I been more anxious lately?"
      - "Show me patterns in my notes about X."
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    async def handle(
        self,
        user_id: str,
        user_message: str,
        ctx_text: str,
    ) -> Dict[str, Any]:
        # 1) Call journal tools
        search_tool = TOOL_REGISTRY.get("memory.journal_search")
        recent_tool = TOOL_REGISTRY.get("memory.journal_recent")

        search_results: List[Dict[str, Any]] = []
        recent_entries: List[Dict[str, Any]] = []

        if recent_tool is not None:
            try:
                recent_entries = recent_tool(user_id=user_id, limit=15)  # type: ignore[call-arg]
            except Exception:
                recent_entries = []

        if search_tool is not None:
            try:
                search_results = search_tool(  # type: ignore[call-arg]
                    user_id=user_id,
                    query=user_message,
                    top_k=15,
                )
            except Exception:
                search_results = []

        def format_entries(entries: List[Dict[str, Any]]) -> str:
            lines: List[str] = []
            for e in entries:
                lines.append(
                    f"- {e.get('timestamp', '')}: {e.get('summary', '')}"
                )
            return "\n".join(lines) if lines else "(none)"

        recent_block = format_entries(recent_entries)
        search_block = format_entries(search_results)

        prompt = f"""
{SCRIBE_BASE}

You are acting in your 'archivist' capacity: your job is to analyse
the user's past diary entries and answer meta-questions about them.

User question:
{user_message}

Recent diary entries:
{recent_block}

Diary entries that appear related to this question:
{search_block}

Task:
1. Identify the main themes that are relevant to the user's question.
2. Highlight any noticeable changes or trends over time.
3. Provide 2–3 gentle, practical reflections or next steps.

Keep the answer under 300 words.
Be specific but kind and non-judgmental.
""".strip()

        answer = await self.llm.generate(prompt)

        return {
            "reflection": answer,
            "recent_entries_used": recent_entries,
            "search_results_used": search_results,
        }
