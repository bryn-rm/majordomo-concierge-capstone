"""
ADK entrypoint.

The google-adk config points to `src.adk_app:create_app`,
which should return the root agent (Majordomo).
"""

from src.llm_client import GeminiClient
from src.agents.majordomo import MajordomoAgent
from src.agents.scribe import ScribeAgent
from src.agents.oracle import OracleAgent
from src.agents.sentinel import SentinelAgent
from src.orchestration.graph import MajordomoGraph


def create_app() -> MajordomoAgent:
    """
    Build and return the Majordomo agent wired with all sub-agents.
    ADK will call this when you run `adk run ...`.
    """
    llm = GeminiClient()

    scribe = ScribeAgent(llm_client=llm)
    oracle = OracleAgent(llm_client=llm)
    sentinel = SentinelAgent(llm_client=llm)

    graph = MajordomoGraph(
        scribe=scribe,
        oracle=oracle,
        sentinel=sentinel,
    )

    majordomo = MajordomoAgent(
        llm_client=llm,
        graph=graph,
    )
    return majordomo
