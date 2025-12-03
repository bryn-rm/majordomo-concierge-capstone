# agent.py — ADK root agent shim for the Majordomo concierge

import os
import sys
from pathlib import Path

# Compute the project root (the directory that contains `src/` and this file)
PROJECT_ROOT = Path(__file__).resolve().parent

# Ensure the project root is on sys.path so `import src...` works
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adk_app import create_app  # now this should resolve

# ADK expects a top-level variable called `root_agent`
root_agent = create_app()
