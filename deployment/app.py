# deployment/app.py

import os
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# --------------------------------------------------------------------
# Ensure project root is on sys.path so `src.*` imports work
# --------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --------------------------------------------------------------------
# Load environment variables from .env at the project root
# --------------------------------------------------------------------
dotenv_path = ROOT / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# --------------------------------------------------------------------
# Now we can safely import from src.*
# --------------------------------------------------------------------
from src.llm_client import GeminiClient
from src.agents.majordomo import MajordomoAgent
from src.agents.oracle import OracleAgent
from src.agents.scribe import ScribeAgent
from src.agents.sentinel import SentinelAgent
from src.agents.archivist import ArchivistAgent
from src.orchestration.graph import MajordomoGraph


# --------------------------------------------------------------------
# FastAPI app and request/response models
# --------------------------------------------------------------------
app = FastAPI(title="Majordomo Concierge API")


class ChatRequest(BaseModel):
    user_id: str = "demo-user"
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    raw: Dict[str, Any] | None = None  # optional debug payload


# --------------------------------------------------------------------
# Startup: build the full agent system once
# --------------------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialise the full agent system when the server starts.
    """
    try:
        llm = GeminiClient()
    except Exception as e:
        # Fail loudly if the API key is missing or misconfigured
        raise RuntimeError(f"Failed to init GeminiClient: {e}") from e

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

    app.state.llm = llm
    app.state.archivist = archivist
    app.state.scribe = scribe
    app.state.oracle = oracle
    app.state.sentinel = sentinel
    app.state.graph = graph
    app.state.majordomo = majordomo

    # Simple in-memory conversation store:
    # sessions[session_key] = [{"role": "user"/"assistant", "content": "..."}]
    app.state.sessions: dict[str, list[dict[str, str]]] = {}


# --------------------------------------------------------------------
# /chat endpoint: multi-turn interaction with Majordomo
# --------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    - Maintains simple in-memory conversation history per session_id.
    - Feeds recent history back into Majordomo so the agent is multi-turn.
    """
    majordomo: MajordomoAgent = app.state.majordomo
    sessions: dict[str, list[dict[str, str]]] = app.state.sessions

    # Choose a key for this conversation
    session_key = req.session_id or req.user_id

    # Get existing history for this session
    history = sessions.get(session_key, [])

    # Build a compact conversation context from last N turns
    max_turns = 10
    recent = history[-max_turns:]
    if recent:
        convo_lines = [
            f"{m['role'].upper()}: {m['content']}" for m in recent
        ]
        convo_context = "\n".join(convo_lines)
        message_for_majordomo = (
            "Here is the recent conversation between the user and you:\n"
            f"{convo_context}\n\n"
            "New user message:\n"
            f"{req.message}"
        )
    else:
        message_for_majordomo = req.message

    # Call Majordomo using the thin .handle wrapper
    try:
        result = await majordomo.handle(
            message=message_for_majordomo,
            user_id=req.user_id,
        )
    except AttributeError:
        # Fallback if handle() doesn't exist for some reason
        try:
            result = await majordomo.handle_message(
                user_id=req.user_id,
                message=message_for_majordomo,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in MajordomoAgent.handle_message: {e}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in MajordomoAgent.handle: {e}",
        )

    # Normalise result
    if isinstance(result, str):
        reply_text = result
        raw_payload = None
    elif isinstance(result, dict):
        reply_text = (
            result.get("reply")
            or result.get("answer")
            or result.get("content")
            or str(result)
        )
        raw_payload = result
    else:
        reply_text = str(result)
        raw_payload = None

    # Update in-memory history
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply_text})
    sessions[session_key] = history

    return ChatResponse(reply=reply_text, raw=raw_payload)
