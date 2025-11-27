"""
Tool registry.

Exposes TOOL_REGISTRY: a mapping from logical tool names
to Python callables. This wraps both local and MCP-based tools.
"""

from src.tools.local import math_helpers, approval

# MCP tools will be added later:
# from src.tools.mcp import calendar_mcp, google_search_mcp, home_assistant_mcp

TOOL_REGISTRY = {
    # Local deterministic tools
    "math.add": math_helpers.add_numbers,
    "math.subtract": math_helpers.subtract_numbers,

    # Human-in-the-loop approval
    "human.approve": approval.request_approval,
    # MCP tools will be registered here later.
}
