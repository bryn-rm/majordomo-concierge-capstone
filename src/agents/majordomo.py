# src/agents/majordomo.py

from typing import Dict, Any

from src.orchestration.router import route
from src.orchestration.graph import MajordomoGraph
from src.prompts.system_instructions import MAJORDOMO_BASE


class MajordomoAgent:
    """
    Majordomo (hub) agent.

    - Receives all user messages.
    - Uses router + graph to pick the right internal flow.
    - Then wraps the internal result into a nice, user-facing reply.
    """

    def __init__(self, llm_client, graph: MajordomoGraph):
        self.llm = llm_client
        self.graph = graph
        self.system_prompt = MAJORDOMO_BASE

    async def handle_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Core entrypoint used internally by the system.

        - Routes the message to the appropriate internal flow.
        - Executes the MajordomoGraph.
        - Asks the LLM to compose a final user-facing reply.
        """
        # Figure out intent + flow
        decision = route(message)

        # Run the internal flow
        result, trace = await self.graph.run(
            flow=decision.flow,
            user_id=user_id,
            user_message=message,
        )

        # Let Gemini write the final reply in Majordomo's voice
        prompt = f"""
{self.system_prompt}

User message:
{message}

Internal result (from specialists):
{result}

Flow trace:
{trace}

Write a concise, user-facing reply that:
- Restates the key thing you did.
- Presents the result clearly.
- Mentions any useful next step or how the user might follow up.
Keep it under 300 words.
""".strip()

        reply_text = await self.llm.generate(prompt)

        return {
            "reply": reply_text,
            "trace": trace,
            "specialist_result": result,
        }

    async def handle(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Thin convenience wrapper used by external callers (FastAPI, UI, etc.).

        FastAPI calls this:

            await majordomo.handle(message=req.message, user_id=req.user_id)

        Internally we just delegate to `handle_message` to keep a single
        place where the core logic lives.
        """
        return await self.handle_message(user_id=user_id, message=message)
