from enum import Enum
from typing import Any, Dict, Tuple

from src.agents.scribe import ScribeAgent
from src.agents.oracle import OracleAgent
from src.agents.sentinel import SentinelAgent
from src.memory import get_dynamic_context
from src.prompts.dynamic_context import format_dynamic_context


class FlowName(str, Enum):
    KNOWLEDGE = "knowledge"
    DIARY_CAPTURE = "diary_capture"
    DIARY_REFLECTION = "diary_reflection"
    SMART_HOME = "smart_home"


class MajordomoGraph:
    """
    High-level orchestrator for Majordomo.

    Given:
      - a FlowName
      - user_id
      - user_message

    It:
      - pulls memory context
      - calls the appropriate agent(s)
      - returns (result, trace)
    """

    def __init__(
        self,
        scribe: ScribeAgent,
        oracle: OracleAgent,
        sentinel: SentinelAgent,
    ):
        self.scribe = scribe
        self.oracle = oracle
        self.sentinel = sentinel

    async def run(
        self,
        flow: FlowName,
        user_id: str,
        user_message: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        trace: Dict[str, Any] = {
            "flow": flow.value,
            "agents": [],
            "tools": [],
        }

        ctx_struct = get_dynamic_context(
            user_id=user_id,
            intent=flow.value,  # type: ignore[arg-type]
            query=user_message,
        )
        ctx_text = format_dynamic_context(ctx_struct)

        if flow == FlowName.KNOWLEDGE:
            trace["agents"].append("oracle")
            result = await self.oracle.handle(user_message, ctx_text)

        elif flow == FlowName.DIARY_CAPTURE:
            trace["agents"].append("scribe")
            result = await self.scribe.capture_entry(user_id, user_message, ctx_text)

        elif flow == FlowName.DIARY_REFLECTION:
            trace["agents"].append("scribe")
            result = await self.scribe.reflect(user_id, user_message, ctx_text)

        elif flow == FlowName.SMART_HOME:
            trace["agents"].append("sentinel")
            result = await self.sentinel.handle(user_id, user_message, ctx_text)

        else:
            result = {"message": "Unsupported flow."}

        return result, trace
