from src.llm_client import GeminiClient
from src.agents.majordomo import MajordomoAgent
from src.agents.scribe import ScribeAgent
from src.agents.oracle import OracleAgent
from src.agents.sentinel import SentinelAgent
from src.agents.archivist import ArchivistAgent
from src.orchestration.graph import MajordomoGraph


def create_app() -> MajordomoAgent:
    llm = GeminiClient()

    archivist = ArchivistAgent(llm_client=llm)
    scribe = ScribeAgent(llm_client=llm, archivist=archivist)
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
