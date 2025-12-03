from typing import Any, Dict, Tuple, Union

from src.agents.scribe import ScribeAgent
from src.agents.oracle import OracleAgent
from src.agents.sentinel import SentinelAgent
from src.memory import get_dynamic_context
from src.prompts.dynamic_context import format_dynamic_context
from src.orchestration.router import FlowName as RouterFlowName


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
        flow: Union[RouterFlowName, str],
        user_id: str,
        user_message: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        trace: Dict[str, Any] = {
            "flow": flow.value if hasattr(flow, "value") else str(flow),
            "agents": [],
            "tools": [],
        }

        flow_value = flow.value if hasattr(flow, "value") else str(flow)

        # Map router flow to memory intent for context fetching
        if flow_value in ("journal", "diary_capture", "diary_reflection"):
            context_intent = "diary_reflection"
        elif flow_value in ("home", "smart_home"):
            context_intent = "smart_home"
        else:
            context_intent = "knowledge"

        ctx_struct = get_dynamic_context(
            user_id=user_id,
            intent=context_intent,  # type: ignore[arg-type]
            query=user_message,
        )
        ctx_text = format_dynamic_context(ctx_struct)

        if flow_value == RouterFlowName.KNOWLEDGE.value:
            trace["agents"].append("oracle")
            result = await self.oracle.handle(user_message, ctx_text)

        elif flow_value in (
            RouterFlowName.JOURNAL.value,
            "diary_capture",
            "diary_reflection",
        ):
            trace["agents"].append("scribe")
            # Scribe internally classifies between schedule/log/reflect
            result = await self.scribe.handle(user_id, user_message, ctx_text)

        elif flow_value == RouterFlowName.HOME.value or flow_value == "smart_home":
            trace["agents"].append("sentinel")
            result = await self.sentinel.handle(user_id, user_message, ctx_text)

        else:
            # Fallback to Oracle so the user still gets a response
            trace["agents"].append("oracle")
            result = await self.oracle.handle(user_message, ctx_text)

        # Track any tool used by downstream agents (e.g., Oracle's search tool)
        tool_used = result.get("tool_used")
        if tool_used:
            trace["tools"].append(tool_used)
        tools_used = result.get("tools_used") or []
        for t in tools_used:
            if t not in trace["tools"]:
                trace["tools"].append(t)

        return result, trace
