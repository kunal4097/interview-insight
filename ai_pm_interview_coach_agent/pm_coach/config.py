"""
App-wide constants: file paths, Granola API endpoints, the provider/model registry, and the
fixed option lists (question types, reported outcomes) used by both the sidebar and the
assessment prompt. Also _remembered_api_key, the secrets.toml/env-var lookup the sidebar
uses so a key only needs to be pasted once.
"""
import os

import streamlit as st


# Two levels up: this file lives in pm_coach/, one directory below the app's real root
# (where pm_interview_coach.py and progress_log.md live) - __file__ here is
# .../ai_pm_interview_coach_agent/pm_coach/config.py, so a single dirname() would resolve
# APP_DIR to pm_coach/ itself and write the log one directory too deep.
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(APP_DIR, "progress_log.md")
GRANOLA_BASE_URL = "https://public-api.granola.ai/v1"
GRANOLA_MCP_URL = "https://mcp.granola.ai/mcp"

PROVIDERS = ["Claude (Anthropic)", "OpenAI"]

CLAUDE_MODELS = {
    "Claude Haiku 4.5 (fastest/cheapest)": "claude-haiku-4-5",
    "Claude Sonnet 5 (recommended)": "claude-sonnet-5",
    "Claude Opus 5 (deepest analysis)": "claude-opus-5",
}

OPENAI_MODELS = {
    "GPT-5 Mini (fastest/cheapest)": "gpt-5-mini",
    "GPT-5.6 Terra (recommended)": "gpt-5.6-terra",
    "GPT-5.6 Sol (deepest analysis)": "gpt-5.6-sol",
}

MODELS_BY_PROVIDER = {"Claude (Anthropic)": CLAUDE_MODELS, "OpenAI": OPENAI_MODELS}

QUESTION_TYPES = [
    "Product sense / design",
    "Product improvement",
    "Analytics / metrics",
    "RCA / business interpretation",
    "Experimentation",
    "Strategy / prioritization",
    "Technical / systems problem-solving",
    "Behavioral / experience",
    "AI product experience",
]

OUTCOME_OPTIONS = [
    "Not provided",
    "Advanced / moved to next round",
    "Received offer",
    "Rejected",
    "Still waiting to hear back",
    "Other (describe below)",
]


def _remembered_api_key(secret_name: str) -> str:
    """Checks .streamlit/secrets.toml first (gitignored, survives restarts and new browser
    tabs), then the env var - so a key only needs to be entered once, not on every run."""
    try:
        value = st.secrets.get(secret_name)
        if value:
            return value
    except Exception:
        pass
    return os.environ.get(secret_name, "")
