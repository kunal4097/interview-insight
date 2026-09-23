"""
AI PM Interview Assessment Coach
Turns Granola notes and/or a transcript of a PM interview into an anonymous,
evidence-backed assessment report: a rating dashboard across reasoning,
communication, delivery, and interviewer response; a question-by-question
breakdown against the rubric that fits each question type; an improved
answer rewrite; a practice plan; and the top evidence-backed issues to fix.
Tracks recurring issues across sessions in a local log.

This file is only the entry point: page config, the sidebar (provider/API key/model), and
dispatch on st.session_state["view"]. Everything else lives in the pm_coach/ package next to
this file - see pm_coach/__init__.py for a map of what's in each module.
"""

import streamlit as st

from pm_coach.config import MODELS_BY_PROVIDER, PROVIDERS, _remembered_api_key
from pm_coach.design_tokens import FONT_SANS, TEXT_SECONDARY, _inject_design_system
from pm_coach.view_add_source import render_add_source_view
from pm_coach.view_assessment import render_report_view, render_review_view
from pm_coach.view_library import render_library_view, render_past_detail_view

st.set_page_config(page_title="AI PM Interview Coach", page_icon="🎯", layout="wide")
_inject_design_system()

with st.sidebar:
    st.header("🔑 Settings")
    provider = st.radio("Model provider", PROVIDERS, horizontal=True, key="sidebar_provider_radio")
    secret_name = "OPENAI_API_KEY" if provider == "OpenAI" else "ANTHROPIC_API_KEY"
    if provider == "OpenAI":
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=_remembered_api_key("OPENAI_API_KEY"),
            help="Get one at https://platform.openai.com/api-keys.",
            key="sidebar_openai_api_key",
        )
    else:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=_remembered_api_key("ANTHROPIC_API_KEY"),
            help="Get one at https://console.anthropic.com/settings/keys.",
            key="sidebar_anthropic_api_key",
        )
    if not api_key:
        st.caption(
            f"⚠️ Add `{secret_name}` to `.streamlit/secrets.toml` once (see README) so you never "
            "have to paste this again, even after a server restart."
        )
    models_for_provider = MODELS_BY_PROVIDER[provider]
    model_label = st.selectbox("Model", list(models_for_provider.keys()), key="sidebar_model_select")
    model = models_for_provider[model_label]
    st.divider()
    st.caption(f"Notes/transcripts stay local to this app - the only network call is to the {provider} API.")
    st.caption("Reports are written to omit names, contact details, employers, and other identifying background.")

st.markdown(
    f'<div style="font-family:{FONT_SANS};font-size:13px;color:{TEXT_SECONDARY};padding:2px 0 14px;">'
    "🎯 AI PM Interview Coach · a quieter way to prep for your next one</div>",
    unsafe_allow_html=True,
)

# One continuous workspace instead of separate tabs - the library (past sessions) is the
# home view; everything else (add a source, review, report) is a step reached from it and
# always has a way back.
view = st.session_state.get("view", "library")

if view == "report":
    render_report_view()
elif view == "review":
    render_review_view(provider, api_key, model)
elif view == "past_detail":
    render_past_detail_view()
elif view == "library":
    render_library_view(provider, api_key, model)
else:  # "add_source"
    render_add_source_view(provider, api_key, model)
