"""
The two views that center on a single assessment: render_report_view() (the finished report,
"report" `view` state) and render_review_view() (the pre-run confirmation card - transcript +
optional target role/outcome/question context - shown after picking a REST note or MCP
meeting, "review" `view` state). Both eventually hand off to run_assessment_flow(); the only
thing this module owns is the confirm-before-running and view-the-result UI around it.
"""
import streamlit as st

from .assessment_flow import run_assessment_flow
from .config import OUTCOME_OPTIONS
from .dashboard import render_last_report
from .granola_mcp import _meeting_title
from .granola_rest import format_granola_transcript
from .ui_components import _review_card_header_html


def render_report_view() -> None:
    """The "report" view: a dedicated result screen (not appended below an ever-growing
    page). Starting a new assessment clears the current selection/report but keeps the
    Granola connection and its loaded call list alive.
    """
    # A dedicated result screen, not the report appended below an ever-growing page -
    # starting a new assessment clears the current selection/report but keeps the Granola
    # connection and its loaded call list alive, so "back to see all the calls" is instant.
    if st.button("← Start a new assessment", key="report_back_btn"):
        for k in [
            "last_report", "last_report_truncated", "last_signals", "last_report_time",
            "granola_selected_note", "granola_mcp_selected_meeting", "mcp_pulled_summary", "mcp_pulled_transcript",
        ]:
            st.session_state.pop(k, None)
        st.session_state["view"] = "library"
        st.rerun()
    render_last_report("assessment")



def render_review_view(provider: str, api_key: str, model: str) -> None:
    """The "review" view: the confirmation step between "picked a call" and "ran the
    assessment" - see the actual transcript before committing, with an explicit way back.
    Branches on which of the three sources (REST note, MCP meeting, MCP raw-console pull)
    populated session_state.
    """
    # The confirmation step between "picked a call" and "ran the assessment" - see the
    # actual transcript that will be assessed before committing, with an explicit way back.
    if st.button("← Back to calls", key="review_back_btn"):
        for k in ["granola_selected_note", "granola_mcp_selected_meeting", "mcp_pulled_summary", "mcp_pulled_transcript"]:
            st.session_state.pop(k, None)
        st.session_state["view"] = "add_source"
        st.rerun()

    selected_note = st.session_state.get("granola_selected_note")
    selected_meeting = st.session_state.get("granola_mcp_selected_meeting")

    if selected_note:
        title = selected_note.get("title") or "Untitled interview"
        g_summary = selected_note.get("summary_markdown") or selected_note.get("summary_text") or ""
        transcript_items = selected_note.get("transcript")
        g_transcript = format_granola_transcript(transcript_items) if transcript_items else ""

        with st.container(border=True):
            st.markdown(_review_card_header_html(title, "From your Granola API key"), unsafe_allow_html=True)

            if g_summary:
                st.markdown(f'<div class="pmic-eyebrow" style="margin-top:6px;">Summary</div>', unsafe_allow_html=True)
                st.markdown(g_summary)
            else:
                st.caption("No summary available for this interview.")

            st.markdown('<div class="pmic-eyebrow" style="margin-top:10px;">Transcript</div>', unsafe_allow_html=True)
            if not g_transcript:
                st.caption(
                    "No transcript for this interview - the assessment will run on the summary "
                    "alone. Verbal-delivery ratings will come back \"Not assessable.\""
                )
            else:
                st.text_area("Transcript", value=g_transcript, height=260, key="review_rest_transcript_display", disabled=True, label_visibility="collapsed")
                st.caption(f"{len(g_transcript)} characters")

            with st.expander("Additional context (optional, but improves the assessment)"):
                g_col1, g_col2 = st.columns(2)
                with g_col1:
                    g_target_role = st.text_input("Target role", key="g_target_role", placeholder="e.g. Senior PM, Growth")
                with g_col2:
                    g_outcome = st.selectbox("Candidate-reported outcome", OUTCOME_OPTIONS, key="g_outcome")
                g_question_context = st.text_area("Question context", key="g_question_context", height=80)
                g_outcome_other = ""
                if g_outcome == "Other (describe below)":
                    g_outcome_other = st.text_input("Describe the outcome", key="g_outcome_other")

            if st.button("Run analysis", type="primary", use_container_width=True, key="review_rest_run_btn"):
                g_resolved_outcome = g_outcome_other.strip() if g_outcome == "Other (describe below)" and g_outcome_other.strip() else g_outcome
                run_assessment_flow(provider, api_key, model, g_summary, g_transcript, g_target_role, g_question_context, g_resolved_outcome, title)
                st.session_state["view"] = "report"
                st.rerun()

    elif selected_meeting or st.session_state.get("mcp_pulled_summary") or st.session_state.get("mcp_pulled_transcript"):
        title = _meeting_title(selected_meeting) if selected_meeting else "Granola interview (via MCP)"
        with st.container(border=True):
            st.markdown(_review_card_header_html(title, "From Granola via MCP"), unsafe_allow_html=True)

            st.markdown('<div class="pmic-eyebrow" style="margin-top:6px;">Summary</div>', unsafe_allow_html=True)
            mcp_summary = st.text_area(
                "Summary", value=st.session_state.get("mcp_pulled_summary", ""), height=100, key="mcp_summary_field", label_visibility="collapsed"
            )

            st.markdown('<div class="pmic-eyebrow" style="margin-top:10px;">Transcript</div>', unsafe_allow_html=True)
            mcp_transcript = st.text_area(
                "Transcript", value=st.session_state.get("mcp_pulled_transcript", ""), height=260, key="mcp_transcript_field", label_visibility="collapsed"
            )
            st.caption(f"{len(mcp_transcript)} characters")

            with st.expander("Additional context (optional, but improves the assessment)"):
                mcp_col1, mcp_col2 = st.columns(2)
                with mcp_col1:
                    mcp_target_role = st.text_input("Target role", key="mcp_target_role", placeholder="e.g. Senior PM, Growth")
                with mcp_col2:
                    mcp_outcome = st.selectbox("Candidate-reported outcome", OUTCOME_OPTIONS, key="mcp_outcome")
                mcp_question_context = st.text_area("Question context", key="mcp_question_context", height=80)
                mcp_outcome_other = ""
                if mcp_outcome == "Other (describe below)":
                    mcp_outcome_other = st.text_input("Describe the outcome", key="mcp_outcome_other")

            if st.button("Run analysis", type="primary", use_container_width=True, key="review_mcp_run_btn"):
                mcp_resolved_outcome = mcp_outcome_other.strip() if mcp_outcome == "Other (describe below)" and mcp_outcome_other.strip() else mcp_outcome
                run_assessment_flow(provider, api_key, model, mcp_summary, mcp_transcript, mcp_target_role, mcp_question_context, mcp_resolved_outcome, title)
                st.session_state["view"] = "report"
                st.rerun()

    else:
        # No selection to review (e.g. a stale rerun) - bounce back to the source picker
        # rather than showing an empty screen.
        st.session_state["view"] = "add_source"
        st.rerun()
