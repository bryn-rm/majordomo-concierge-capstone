"""
Tool registry.

Exposes TOOL_REGISTRY: a mapping from logical tool names
to Python callables. This wraps both local and MCP-based tools.
"""

from src.tools.local import math_helpers, approval, journal_tools, calendar_local
from src.tools.mcp import google_search_mcp, wikipedia_mcp, calendar_mcp, home_assistant_mcp

TOOL_REGISTRY = {
    # Local deterministic tools
    "math.add": math_helpers.add_numbers,
    "math.subtract": math_helpers.subtract_numbers,

    # Human-in-the-loop approval
    "human.approve": approval.request_approval,

    # Search tools
    "search.google": google_search_mcp.google_search,
    "search.wikipedia": wikipedia_mcp.wikipedia_search,

    # Calendar tools
    # Real Google Calendar:
    "calendar.add_event": calendar_mcp.add_event,
    "calendar.list_upcoming": calendar_mcp.list_upcoming_events,
    # Local test versions:
    "calendar.local_add": calendar_local.add_event,
    "calendar.local_list": calendar_local.list_upcoming_events,

    # Journal memory tools
    "memory.journal_recent": journal_tools.recent_journal_entries,
    "memory.journal_search": journal_tools.search_journal_entries,

    # Smart home / Home Assistant (simulated)
    "smarthome.get_state": home_assistant_mcp.get_home_state,
    "smarthome.set_state": home_assistant_mcp.set_home_state,
}
