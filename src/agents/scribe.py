# src/agents/scribe.py

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Literal

from src.prompts.system_instructions import SCRIBE_BASE
from src.memory.journal_store import save_entry
from src.agents.archivist import ArchivistAgent
from src.tools import TOOL_REGISTRY

Mode = Literal["schedule", "log", "reflect"]


class ScribeAgent:
    """
    Scribe agent.

    Responsibilities:
    - "Log / diary" mode: capture free-form notes and summarise them.
    - "Schedule" mode: interpret scheduling language and create calendar events
      using an LLM to extract structured event details.
    - "Reflect" mode: analyse past notes (via Archivist where available).
    """

    def __init__(self, llm_client, archivist: Optional[ArchivistAgent] = None):
        self.llm = llm_client
        self.archivist = archivist

    # -------------------------------------------------------------------------
    # Public entry point used by MajordomoGraph
    # -------------------------------------------------------------------------
    async def handle(
        self,
        user_id: str,
        user_message: str,
        ctx_text: str = "",
    ) -> Dict[str, Any]:
        """
        Main entry point.

        1. Classify intent: schedule vs log vs reflect.
        2. Dispatch to the appropriate internal method.
        """
        mode = self._classify_mode(user_message)

        if mode == "schedule":
            result = await self._schedule_event(user_id=user_id, user_message=user_message)
            result["mode"] = "schedule"
            result.setdefault("tools_used", [])
            return result

        if mode == "log":
            result = await self.capture_entry(
                user_id=user_id,
                user_message=user_message,
                ctx_text=ctx_text,
            )
            result["mode"] = "log"
            result.setdefault("tools_used", [])
            return result

        # default: reflection over existing notes
        result = await self.reflect(
            user_id=user_id,
            user_message=user_message,
            ctx_text=ctx_text,
        )
        result["mode"] = "reflect"
        result.setdefault("tools_used", [])
        return result

    # -------------------------------------------------------------------------
    # Intent classification
    # -------------------------------------------------------------------------
    def _classify_mode(self, user_message: str) -> Mode:
        """
        Very lightweight heuristic classifier for Scribe:

        - If there is strong scheduling language → "schedule"
        - Else if the user explicitly says 'log', 'note', 'diary', etc. → "log"
        - Else → "reflect"
        """
        text = user_message.lower()

        scheduling_keywords = [
            "add to my calendar",
            "add this to my calendar",
            "add it to my calendar",
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
            "calendar",
            "meeting",
            "appointment",
            "dinner with",
            "call with",
        ]

        log_keywords = [
            "log:",
            "log ",
            "diary",
            "journal",
            "note to self",
            "write this down",
            "record this",
            "remember that",
        ]

        if any(kw in text for kw in scheduling_keywords):
            return "schedule"

        if any(kw in text for kw in log_keywords):
            return "log"

        if any(x in text for x in ["reflect", "pattern", "trend", "lately", "recent notes"]):
            return "reflect"

        return "reflect"

    # -------------------------------------------------------------------------
    # Scheduling / calendar integration (LLM-based)
    # -------------------------------------------------------------------------
    async def _schedule_event(
        self,
        user_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Use an LLM to extract a structured event object and then call
        the calendar.create_event tool.

        The LLM is responsible for:
        - Interpreting the natural language
        - Normalising to ISO 8601 strings (without timezone)
        """
        create_event_tool = TOOL_REGISTRY.get("calendar.create_event")
        tools_used: list[str] = []

        if create_event_tool is None:
            return {
                "parsed_event": None,
                "event_id": None,
                "tools_used": tools_used,
                "note": (
                    "I tried to schedule this, but my calendar tool isn't available. "
                    "You may need to add it manually for now."
                ),
            }

        # ---- LLM: extract structured event spec ----
        extraction_prompt = f"""
{SCRIBE_BASE}

You are the Scribe, responsible for turning user scheduling requests
into precise calendar events.

The user says:
\"\"\"{user_message}\"\"\"


1. Carefully infer:
   - A short, human-friendly title summarising the event.
   - A start datetime.
   - An end datetime (if none is given, default to 1 hour after start).

2. Normalise both datetimes to ISO 8601 format WITHOUT timezone offsets,
   in the exact form: YYYY-MM-DDTHH:MM:SS
   Examples:
   - "2025-12-12T19:00:00"
   - "2025-06-01T09:30:00"

3. If you truly cannot infer a start date/time at all, set "start_iso"
   to null and "end_iso" to null, but do this only as a last resort.
   Prefer **making a reasonable assumption** over returning null.

4. ALWAYS respond with a single, strictly valid JSON object and nothing else.
   The JSON must have exactly these keys:
   - "title": string
   - "start_iso": string or null
   - "end_iso": string or null

Examples of valid JSON responses:
{{
  "title": "Dinner with Annie",
  "start_iso": "2025-12-12T19:00:00",
  "end_iso": "2025-12-12T21:00:00"
}}

{{
  "title": "Call with therapist",
  "start_iso": "2025-11-10T15:30:00",
  "end_iso": "2025-11-10T16:30:00"
}}
""".strip()

        raw = await self.llm.generate(extraction_prompt)

        # Try to extract JSON from the model's response robustly
        event_spec = self._parse_event_json(raw)

        if event_spec is None:
            return {
                "parsed_event": None,
                "event_id": None,
                "tools_used": tools_used,
                "note": (
                    "I tried to interpret your scheduling request with my LLM-based planner, "
                    "but I couldn't extract a usable date/time. "
                    "Please try again with something like: "
                    "'Dinner with Annie on 2025-12-12 from 19:00 to 22:00'."
                ),
            }

        title = event_spec.get("title") or user_message
        start_iso = event_spec.get("start_iso")
        end_iso = event_spec.get("end_iso")

        # If the LLM didn't give a start time, we genuinely can't schedule.
        if not start_iso:
            return {
                "parsed_event": event_spec,
                "event_id": None,
                "tools_used": tools_used,
                "note": (
                    "My LLM planner couldn't confidently infer any start time at all "
                    "from your message, so I didn't create an event. "
                    "Try including an explicit date and time."
                ),
            }

        # If end is missing, default to +1 hour
        if not end_iso:
            try:
                dt_start = datetime.fromisoformat(start_iso)
                dt_end = dt_start + timedelta(hours=1)
                end_iso = dt_end.isoformat()
            except Exception:
                # If parsing fails, still fall back to simple 1-hour string tweak
                # to avoid total failure.
                end_iso = start_iso  # 0-length event is acceptable for demo

        # Call the calendar tool
        try:
            event_id = create_event_tool(
                user_email=None,  # could be mapped from user_id later
                title=title,
                start_iso=start_iso,
                end_iso=end_iso,
                description=f"Created by Scribe for user {user_id}",
            )
            tools_used.append("calendar.create_event")
            note = "Event created successfully in your calendar."
        except Exception as e:
            event_id = None
            note = f"Attempted to create the event but hit an error: {e!r}"

        return {
            "parsed_event": {
                "title": title,
                "start_iso": start_iso,
                "end_iso": end_iso,
            },
            "event_id": event_id,
            "tools_used": tools_used,
            "note": note,
        }

    def _parse_event_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """
        Extract a JSON object from the LLM's response.

        - Tries direct json.loads.
        - If that fails, looks for the first {...} block and tries again.
        """
        raw = raw.strip()

        # Fast path: it's just JSON
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        # Fallback: find first JSON-looking substring
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(raw[start : end + 1])
                if isinstance(obj, dict):
                    return obj
            except Exception:
                return None

        return None

    # -------------------------------------------------------------------------
    # Diary / logging
    # -------------------------------------------------------------------------
    async def capture_entry(
        self,
        user_id: str,
        user_message: str,
        ctx_text: str,
    ) -> Dict[str, Any]:
        """
        Take a raw diary message, generate a summary + tags, and store it.
        """
        lower = user_message.lower()
        if lower.startswith("log:"):
            raw_text = user_message[4:].strip()
        elif lower.startswith("log "):
            raw_text = user_message[4:].strip()
        else:
            raw_text = user_message.strip()

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

    # -------------------------------------------------------------------------
    # Reflection
    # -------------------------------------------------------------------------
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
