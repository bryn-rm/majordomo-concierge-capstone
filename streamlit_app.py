# streamlit_app.py

import uuid
import httpx
from datetime import datetime

import streamlit as st

# URL of your FastAPI backend
BACKEND_URL = "http://127.0.0.1:8000/chat"

# --------------------------
# Page config & layout
# --------------------------
st.set_page_config(
    page_title="Majordomo Concierge",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Majordomo Concierge")
st.caption("Multi-agent life concierge (Oracle • Scribe • Sentinel)")

# --------------------------
# Session state
# --------------------------
if "messages" not in st.session_state:
    # List of dicts: {"role": "user" | "assistant", "content": str, "meta": {...}}
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{uuid.uuid4()}"

if "user_id" not in st.session_state:
    st.session_state.user_id = "bryn"  # you can expose this in sidebar later

if "last_raw" not in st.session_state:
    st.session_state.last_raw = None


# --------------------------
# Sidebar controls
# --------------------------
with st.sidebar:
    st.subheader("Session")
    st.write(f"**User ID:** `{st.session_state.user_id}`")
    st.write(f"**Session ID:** `{st.session_state.session_id}`")

    if st.button("🧹 Reset conversation"):
        st.session_state.messages = []
        st.session_state.session_id = f"session-{uuid.uuid4()}"
        st.session_state.last_raw = None
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Debug / Trace")

    if st.session_state.last_raw is not None:
        trace = st.session_state.last_raw.get("trace")
        specialist = st.session_state.last_raw.get("specialist_result")
        st.markdown("**Flow trace:**")
        st.json(trace)

        if specialist is not None:
            with st.expander("Specialist raw result"):
                st.json(specialist)
    else:
        st.caption("Send a message to see trace/debug info here.")


# --------------------------
# Chat history display
# --------------------------
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]

    if role == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(content)


# --------------------------
# Helper to call backend
# --------------------------
def send_to_backend(message: str) -> tuple[str, dict | None]:
    """
    Send a single turn to the FastAPI /chat endpoint and return (reply_text, raw_dict).
    """
    payload = {
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.session_id,
        "message": message,
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(BACKEND_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Expected keys: "reply" and optional "raw"
    reply_text = data.get("reply", "")
    raw = data.get("raw", None)
    return reply_text, raw


# --------------------------
# Chat input
# --------------------------
prompt = st.chat_input("Talk to Majordomo...")

if prompt:
    # 1. Add user message to history
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "meta": {"timestamp": datetime.utcnow().isoformat()},
        }
    )

    # Re-render the user message immediately
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # 2. Call backend
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Majordomo is thinking..."):
            try:
                reply, raw = send_to_backend(prompt)
            except Exception as e:
                reply = f"⚠️ Error talking to backend: `{e}`"
                raw = None

            st.markdown(reply)

    # 3. Save assistant message + raw debug
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    )
    st.session_state.last_raw = raw
