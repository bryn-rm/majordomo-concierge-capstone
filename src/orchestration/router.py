from dataclasses import dataclass
from typing import Literal

from src.orchestration.graph import FlowName

IntentLiteral = Literal[
    "knowledge",
    "diary_capture",
    "diary_reflection",
    "smart_home",
]


@dataclass
class RoutingDecision:
    intent: IntentLiteral
    flow: FlowName


def route(user_message: str) -> RoutingDecision:
    """
    Heuristic router.
    Later you can swap this for an LLM-based classifier if you want.
    """
    lower = user_message.lower().strip()

    # Diary capture
    if lower.startswith("log:") or lower.startswith("note:") or "diary" in lower:
        return RoutingDecision(intent="diary_capture", flow=FlowName.DIARY_CAPTURE)

    # Diary reflection / meta-questions about past entries
    if any(
        phrase in lower
        for phrase in [
            "what have i been saying about",
            "what have i said about",
            "show me patterns in my notes",
            "show me patterns in my diary",
            "have i been more",
            "have i been less",
            "how often do i talk about",
            "what do my notes say about",
            "patterns in my entries",
            "recent entries",
            "journal",
            "past notes",
        ]
    ):
        return RoutingDecision(intent="diary_reflection", flow=FlowName.DIARY_REFLECTION)

    # Smart home
    if any(
        phrase in lower
        for phrase in [
            "lights",
            "thermostat",
            "smart home",
            "lock the door",
            "lock the doors",
            "unlock the door",
            "doors",
        ]
    ):
        return RoutingDecision(intent="smart_home", flow=FlowName.SMART_HOME)

    # Default: knowledge
    return RoutingDecision(intent="knowledge", flow=FlowName.KNOWLEDGE)
