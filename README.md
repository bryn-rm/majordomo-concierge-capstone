# Majordomo Concierge Capstone

Multi-agent concierge built with Google's Agent Development Kit (ADK).

This project implements:

- **Majordomo** – hub agent that talks to the user and routes requests.
- **Oracle** – knowledge agent using search / grounding tools.
- **Scribe** – diary and notes agent with memory.
- **Sentinel** – smart home / IoT agent with safety guardrails.

## Project goals

- Showcase a realistic concierge-style AI that can:
  - Answer grounded questions (Oracle)
  - Capture and reflect on diary entries (Scribe)
  - Simulate smart home actions with safety (Sentinel)
- Use Google ADK as the runtime, with `adk web` for interaction.
- Be structured and testable enough to feel like a small real system.
