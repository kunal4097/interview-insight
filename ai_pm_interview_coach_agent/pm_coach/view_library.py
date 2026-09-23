"""
The two views that center on the session log: render_library_view() (the home/default view -
every past session as a card, "library" `view` state) and render_past_detail_view() (one
session's full stored report, "past_detail" `view` state). Both read progress_log.md through
log_store; render_library_view also drives the cross-session "Summarize recurring issues"
button via llm_client directly (it isn't a per-session assessment, so it doesn't go through
assessment_flow).
"""
import streamlit as st

from .design_tokens import FONT_SANS, FONT_SERIF, TEXT_PRIMARY, TEXT_SECONDARY
from .llm_client import call_llm
from .log_store import _parse_log_entries, read_log
from .prompts import SUMMARY_SYSTEM_PROMPT
from .ui_components import _log_entry_card_html, _section_header_html


def render_past_detail_view() -> None:
    """The "past_detail" view: one logged session's full card + stored body, with an
    explicit way back - a dedicated screen rather than an inline expander competing with
    everything else on the library page.
    """
    # A dedicated screen for one past logged session - the same card that shows in the
    # library, plus its full stored detail, with an explicit way back rather than an
    # inline expander competing with everything else on the library page.
    if st.button("← Back to library", key="past_detail_back_btn"):
        st.session_state.pop("selected_log_index", None)
        st.session_state["view"] = "library"
        st.rerun()

    log_content = read_log()
    entries = _parse_log_entries(log_content) if log_content.strip() else []
    idx = st.session_state.get("selected_log_index")
    if idx is None or idx >= len(entries):
        st.info("That session is no longer available.")
    else:
        entry = entries[idx]
        st.markdown(_log_entry_card_html(entry), unsafe_allow_html=True)
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown(entry["body"] or "Not available.")



def render_library_view(provider: str, api_key: str, model: str) -> None:
    """The "library" view and home/default screen: the list of past sessions as cards,
    plus the "add an interview" prompts and the cross-session recurring-issues summary.
    """
    log_content = read_log()
    entries = _parse_log_entries(log_content) if log_content.strip() else []

    header_left, header_right = st.columns([5, 2])
    with header_left:
        st.markdown(
            _section_header_html(
                "Your workspace", "Interview library",
                f"{len(entries)} session{'s' if len(entries) != 1 else ''} logged." if entries else "No sessions yet.",
                size="lg",
            ),
            unsafe_allow_html=True,
        )
    with header_right:
        st.write("")
        st.write("")
        if st.button("➕ Add interview", type="primary", use_container_width=True, key="library_add_top"):
            st.session_state["view"] = "add_source"
            st.rerun()

    for i, entry in enumerate(entries):
        st.markdown(_log_entry_card_html(entry), unsafe_allow_html=True)
        btn_col, _rest_col = st.columns([2, 3])
        with btn_col:
            if st.button("View full assessment →", key=f"view_log_{i}", use_container_width=True):
                st.session_state["selected_log_index"] = i
                st.session_state["view"] = "past_detail"
                st.rerun()
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # A persistent "add another" prompt at the end of the list, not just an empty-state
    # message - present whether the library is empty or has a dozen sessions in it. First-run
    # wording ("first interview") only fits when the library is actually empty; once there's
    # a history, the pitch shifts to "another" rather than "first".
    if entries:
        prompt_title = "Add an interview, get the analysis"
        prompt_body = "See what held up, what didn't, and exactly what to practice next."
    else:
        prompt_title = "Learn from your first interview"
        prompt_body = (
            "Add a transcript to see how clearly you answered, how well you explained your "
            "decisions, and what to practise next—with evidence from your conversation."
        )
    with st.container(border=True):
        st.markdown(
            f'<div style="text-align:center;padding:14px 0;">'
            f'<div style="font-family:{FONT_SERIF};font-weight:600;font-size:18px;color:{TEXT_PRIMARY};margin-bottom:6px;">{prompt_title}</div>'
            f'<div style="font-family:{FONT_SANS};font-size:13.5px;color:{TEXT_SECONDARY};">{prompt_body}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        _left_pad, mid_col, _right_pad = st.columns([1, 1, 1])
        with mid_col:
            if st.button("➕ Add an interview", use_container_width=True, key="library_add_bottom"):
                st.session_state["view"] = "add_source"
                st.rerun()

    if entries:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        if st.button("Summarize recurring issues across all sessions", key="library_summarize_btn"):
            if not api_key:
                st.error(f"Add your {provider} API key in the sidebar first.")
            else:
                with st.spinner("Looking for patterns across sessions..."):
                    summary_of_log, _ = call_llm(provider, api_key, model, SUMMARY_SYSTEM_PROMPT, log_content)
                st.markdown(summary_of_log)
        st.download_button(
            "Download full log (.md)",
            data=log_content,
            file_name="progress_log.md",
            mime="text/markdown",
            use_container_width=True,
            key="library_download_log_btn",
        )
