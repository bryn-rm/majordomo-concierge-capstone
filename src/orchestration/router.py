# src/orchestration/router.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class FlowName(str, Enum):
    GENERAL = "general"
    KNOWLEDGE = "knowledge"
    JOURNAL = "journal"   # Scribe / Archivist / calendar
    HOME = "home"         # Sentinel / IoT


@dataclass
class RoutingDecision:
    flow: FlowName
    reason: str


def route(user_message: str) -> RoutingDecision:
    """
    Very simple heuristic router.

    IMPORTANT: Order matters.
    We check for scheduling/journal intents BEFORE knowledge,
    so things like "add X to my calendar" hit Scribe instead of Oracle.
    """
    text = user_message.lower().strip()

    # -------------------------
    # 1. Scheduling / journal
    # -------------------------
    scheduling_phrases = [
        "add to my calendar",
        "add this to my calendar",
        "put this in my calendar",
        "put it in my calendar",
        "schedule",
        "schedule in",
        "schedule this",
        "book in",
        "set a reminder",
        "remind me",
        "create an event",
        "create event",
    ]

    journal_phrases = [
        "journal",
        "diary",
        "note to self",
        "log this",
        "write this down",
        "record this",
        "remember that",
    ]

    # If user mentions calendar at all + an "add/schedule" verb, treat as scheduling
    if "calendar" in text and any(verb in text for verb in ["add", "put", "schedule", "create", "remind"]):
        return RoutingDecision(
            flow=FlowName.JOURNAL,
            reason="calendar + scheduling verb → journal/scheduling flow",
        )

    # Generic scheduling phrases
    if any(phrase in text for phrase in scheduling_phrases):
        return RoutingDecision(
            flow=FlowName.JOURNAL,
            reason="scheduling/reminder intent → journal flow",
        )

    # Generic journalling phrases
    if any(phrase in text for phrase in journal_phrases):
        return RoutingDecision(
            flow=FlowName.JOURNAL,
            reason="journal/diary intent → journal flow",
        )

    # -------------------------
    # 2. Home / IoT (Sentinel)
    # -------------------------
    home_keywords = [
        "lights",
        "light on",
        "light off",
        "thermostat",
        "heating",
        "temperature",
        "aircon",
        "smart plug",
        "lock the door",
        "unlock the door",
        "front door",
        "garage door",
    ]

    if any(kw in text for kw in home_keywords):
        return RoutingDecision(
            flow=FlowName.HOME,
            reason="home/IoT-related intent → sentinel flow",
        )

    # -------------------------
    # 3. Knowledge (Oracle)
    # -------------------------
    knowledge_triggers = [
        "who ",
        "what ",
        "when ",
        "where ",
        "why ",
        "how ",
        "latest",
        "news",
        "update",
        "price",
        "score",
        "result",
        "weather",
        "population",
        "definition",
        "meaning",
        "history",
        "information",
        "info",
    ]

    if "?" in text or any(kw in text for kw in knowledge_triggers):
        return RoutingDecision(
            flow=FlowName.KNOWLEDGE,
            reason="question/information intent → oracle flow",
        )

    # -------------------------
    # 4. Fallback
    # -------------------------
    return RoutingDecision(
        flow=FlowName.GENERAL,
        reason="default → general conversation flow",
    )
