from typing import Dict, Any

from src.prompts.system_instructions import ORACLE_BASE


class OracleAgent:
    """
    Oracle agent.

    - Handles knowledge / information questions.
    - For now, just uses the LLM directly (no external search yet).
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    async def handle(self, user_message: str, context_text: str) -> Dict[str, Any]:
        prompt = f"""
{ORACLE_BASE}

Context:
{context_text}

User question:
{user_message}

Answer briefly, clearly, and honestly.
If you are uncertain, say you are uncertain.
""".strip()

        answer = await self.llm.generate(prompt)
        return {"answer": answer}
