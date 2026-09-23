"""
run_assessment_flow() is the one controller all three "Run analysis" buttons call (manual
paste, Granola REST review, Granola MCP review): validates inputs, calls the model, derives/
resolves the session label, appends to the log, computes conversation signals, and stashes
everything the report view needs into st.session_state. Kept as its own module (rather than
folded into a view) because exactly one copy of this orchestration must run regardless of
which of the three "Run analysis" buttons triggered it.
"""
import os
from datetime import datetime

import streamlit as st

from .config import LOG_PATH
from .llm_client import call_llm
from .log_store import _derive_session_label, append_to_log
from .prompts import SYSTEM_PROMPT
from .report_parsing import build_user_content
from .signals import compute_conversation_signals


def run_assessment_flow(provider: str, api_key: str, model: str, summary: str, transcript: str, target_role: str, question_context: str, outcome: str, session_label: str) -> None:
    if not api_key:
        st.error(f"Add your {provider} API key in the sidebar first.")
        return
    if not summary.strip() and not transcript.strip():
        st.error("Provide an interview summary and/or a transcript first.")
        return
    with st.spinner("Assessing the interview..."):
        user_content = build_user_content(summary, transcript, target_role, question_context, outcome)
        report_md, truncated = call_llm(provider, api_key, model, SYSTEM_PROMPT, user_content)
        resolved_label = session_label.strip() if session_label and session_label.strip() else _derive_session_label(report_md)
        append_to_log(resolved_label, report_md)
    st.session_state["last_report"] = report_md
    st.session_state["last_report_truncated"] = truncated
    st.session_state["last_report_time"] = datetime.now()
    st.session_state["last_signals"] = compute_conversation_signals(transcript)
    if truncated:
        st.warning("The model's response hit its length limit before finishing - the report below may be incomplete. Try running the assessment again.")
    st.success(f"Done. Logged to `{os.path.basename(LOG_PATH)}`.")
