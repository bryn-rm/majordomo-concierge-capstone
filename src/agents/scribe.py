# src/agents/scribe.py

from typing import Dict, Any, Optional

from src.prompts.system_instructions import SCRIBE_BASE
from src.memory.journal_store import save_entry
from src.agents.archivist import ArchivistAgent


class ScribeAgent:
    """
    Scribe agent.

    - Capture diary entries ("Log: ...").
    - For reflection/meta-questions, delegates to ArchivistAgent.
    """

    def __init__(self, llm_client, archivist: Optional[ArchivistAgent] = None):
        self.llm = llm_client
        self.archivist = archivist

    async def capture_entry(
        self,
        user_id: str,
        user_message: str,
        ctx_text: str,
    ) -> Dict[str, Any]:
        """
        Take a raw diary message, generate a summary + tags, and store it.
        """
        raw_text = user_message.lstrip("Log:").lstrip("log:").strip()

        prompt = f"""
{SCRIBE_BASE}

Existing context:
{ctx_text}

New diary entry:
{raw_text}

Task:
1. Write a concise 1–2 sentence summary of the entry.
2. Suggest 3–5 tags (people, places, themes, emotions).

Return ONLY the summary text; tags will be stubbed in v1.
""".strip()

        summary = await self.llm.generate(prompt)
        # v1: stub tags instead of parsing JSON
        tags = ["diary", "v1"]

        entry_id = save_entry(
            user_id=user_id,
            raw_text=raw_text,
            summary=summary,
            tags=tags,
        )

        return {
            "entry_id": entry_id,
            "summary": summary,
            "tags": tags,
        }

    async def reflect(
        self,
        user_id: str,
        user_message: str,
        ctx_text: str,
    ) -> Dict[str, Any]:
        """
        Reflect over past entries.

        For now, this simply delegates to Archivist if available.
        If no Archivist is set, falls back to a simpler reflection using ctx_text.
        """
        if self.archivist is not None:
            return await self.archivist.handle(
                user_id=user_id,
                user_message=user_message,
                ctx_text=ctx_text,
            )

        # Fallback: use only the context block (recent entries already embedded in ctx_text)
        prompt = f"""
{SCRIBE_BASE}

Context (user profile + recent diary entries):
{ctx_text}

User request:
{user_message}

Task:
1. Identify 2–4 recurring themes in the user's recent notes.
2. Describe any noticeable changes over time.
3. Suggest 2–3 gentle, practical next steps or reflection questions.

Keep it under 250 words.
""".strip()

        reflection = await self.llm.generate(prompt)
        return {"reflection": reflection}
