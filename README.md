🧠 Majordomo — Multi-Agent AI Concierge System

A fully extensible, tool-using agentic architecture built with Gemini, FastAPI, Streamlit, and Google Calendar OAuth.

🚀 Overview

Majordomo is a multi-agent AI concierge designed to help users manage knowledge, memory, tasks, calendar events, journaling, and contextual reasoning in a unified system.
It uses an orchestration graph to route user messages to specialized agents:

🧩 Agents
Agent	Purpose
Majordomo (Hub)	Central controller — routes messages and composes final responses.
Oracle	Handles factual + time-sensitive knowledge queries using Google Search & Wikipedia tools.
Scribe	Captures diary entries, summarises notes, and performs reflective analysis.
Sentinel	Handles safety- or boundaries-related interactions.
Archivist	Supports deep memory/reflection queries.
🔧 Integrated Tools
Tool	Description
Google Search MCP	Fetches real-time search results via Google Custom Search API.
Wikipedia MCP	Retrieves background knowledge for non-time-sensitive queries.
Google Calendar MCP	Adds and lists calendar events using OAuth2.
Local Tools	Math helper, approval logic, journal store, profile store, etc.
🖥️ Frontend + Backend

FastAPI backend (/chat endpoint) for multi-turn interaction

Streamlit UI for a clean chat interface

Full stateful multi-turn conversations

Fully async execution for tool calls + LLM inference

✨ Key Features
✅ 1. Intelligent Routing & Orchestration

Every message runs through a router → graph → specialist agent → final Gemini summarisation.

✅ 2. Real Tool Usage

Oracle now genuinely calls:

google_search_mcp.search()

wikipedia_mcp.search()

Majordomo shows tool traces and uses results in final summarisation.

✅ 3. Calendar Integration

Fully working Google Calendar OAuth — user can say:

“Add dinner with Annie on December 12th, 2025 from 7–10pm”

Majordomo → Scribe → Calendar MCP → Event is created.

✅ 4. Memory + Journaling

Scribe stores diary entries with summaries and tags.
Archivist offers meta-reflection across time.

✅ 5. Streamlit Chat UI

A simple, attractive frontend with:

Multi-turn chat

Display of traces

Display of specialist results

Nice polished UX

📁 Repository Structure
project/
  ├── src/
  │   ├── agents/
  │   │   ├── majordomo.py
  │   │   ├── oracle.py
  │   │   ├── scribe.py
  │   │   ├── sentinel.py
  │   │   └── archivist.py
  │   ├── tools/
  │   │   ├── mcp/
  │   │   │   ├── google_search_mcp.py
  │   │   │   ├── wikipedia_mcp.py
  │   │   │   └── calendar_mcp.py
  │   │   └── local/
  │   ├── orchestration/
  │   │   ├── graph.py
  │   │   └── router.py
  │   ├── memory/
  │   ├── prompts/
  │   ├── llm_client.py
  │   └── adk_app.py
  ├── deployment/app.py          # FastAPI backend
  ├── streamlit_app.py           # Streamlit UI
  ├── config/credentials.json    # (not committed)
  ├── config/token.json          # (not committed)
  ├── .env
  └── README.md

🔑 Environment Setup
1. Clone the repo
git clone <your-repo-url>
cd majordomo-concierge-capstone

2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Set environment variables

Edit .env:

GEMINI_API_KEY=xxxxx
GOOGLE_SEARCH_API_KEY=xxxxx
GOOGLE_SEARCH_CX=xxxxx

📅 Google Calendar OAuth Setup
Place your credentials:
config/credentials.json

First time authentication:

Run any Calendar tool call, e.g.:

python - <<'EOF'
from src.tools.mcp.calendar_mcp import add_event
print(add_event(None, "Test Event", "2025-12-12T19:00:00"))
EOF


A browser window will open → authenticate → token.json is created.

🧪 Testing the System
Run FastAPI backend:
uvicorn deployment.app:app --reload

Test in browser:
http://localhost:8000/docs

Run Streamlit UI:
streamlit run streamlit_app.py

💬 Example Interactions
✓ Knowledge Query (Oracle)

“Who won the Ashes last year?”

→ Uses Google Search MCP
→ Summarises results

✓ Journaling (Scribe)

“Log: I had a stressful day at work.”

→ Stored with summary + tags

✓ Calendar Interaction

“Add dinner with Annie on December 12th from 7–10pm.”

→ Automatically parsed
→ Writes to Google Calendar

✓ Safety / Boundaries

Sentinel intervenes for inappropriate or unsafe queries.

🧠 Architecture Diagram

(Use your generated robot graphic here as the thumbnail.)

🛠️ Extending the System

Majordomo is designed to be fully modular:

Add new tools by registering functions in TOOL_REGISTRY

Add new agents inside src/agents/

Add new flows in router.py

Modify orchestration in graph.py

🏁 Summary

Majordomo is a robust example of a real, functioning, multi-modal agent system that:

✔ Routes intent
✔ Uses tools intelligently
✔ Stores memory
✔ Writes to external services
✔ Combines multiple agents into a cohesive assistant