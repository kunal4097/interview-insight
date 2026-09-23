"""
The "add_source" view ("Bring an interview to review"): the intake screen where a transcript
enters the app. Two cards, always both visible - manual paste/upload (left) and Granola
connect (right, itself branching on not-connected / REST-key-connected / MCP-connected).
Also owns _render_mcp_raw_console(), the manual "call any tool, see its schema" fallback
console used when a connected MCP server's meetings can't be parsed into a browsable list.
"""
import json

import streamlit as st

from .assessment_flow import run_assessment_flow
from .config import OUTCOME_OPTIONS
from .design_tokens import ACCENT_BLUE_BG, FONT_SANS, FONT_SERIF, TEXT_PRIMARY, TEXT_SECONDARY
from .granola_mcp import (
    GranolaAPIError,
    _clean_mcp_transcript_text,
    _find_meeting_list,
    _meeting_date,
    _meeting_id,
    _meeting_summary,
    _meeting_title,
    _tool_id_arg_name,
    granola_mcp_call_tool,
    granola_mcp_connect,
)
from .granola_rest import granola_get_note, granola_list_all_folders, granola_list_notes, granola_request
from .ui_components import _chip_html, _section_header_html


def _render_mcp_raw_console(tool_names: list, tool_schemas: dict) -> None:
    """Manual fallback for when the browse-and-select flow can't find a recognizable call
    list (or for power users who want to call a different tool directly) - call any tool by
    name, see its real input schema, and pull the raw result into the assessment yourself."""
    st.subheader("Call a tool")
    tool_name = st.selectbox("Tool", tool_names, key="mcp_tool_name")
    st.caption("Input schema (from Granola's MCP server, not guessed):")
    st.json(tool_schemas.get(tool_name, {}))
    args_json = st.text_area(
        "Arguments (JSON)",
        value="{}",
        height=100,
        help="Match property names from the schema above. Most list/read tools accept {} for defaults.",
        key="mcp_raw_args_json",
    )
    if st.button("Call tool", type="primary", key="mcp_raw_call_tool_btn"):
        try:
            arguments = json.loads(args_json) if args_json.strip() else {}
        except json.JSONDecodeError as e:
            st.error(f"Arguments aren't valid JSON: {e}")
        else:
            with st.spinner(f"Calling {tool_name}..."):
                try:
                    result = granola_mcp_call_tool(tool_name, arguments)
                except GranolaAPIError as e:
                    st.error(str(e))
                else:
                    st.session_state["granola_mcp_last_result"] = result

    last_result = st.session_state.get("granola_mcp_last_result")
    if last_result:
        st.divider()
        if last_result["is_error"]:
            st.error(last_result["text"] or "The tool call returned an error.")
        else:
            if last_result["structured"] is not None:
                st.markdown("**Structured result**")
                st.json(last_result["structured"])
            if last_result["text"]:
                st.markdown("**Text result**")
                st.text_area("Raw text", value=last_result["text"], height=200, key="mcp_raw_text_display")

        mcp_pull_text = last_result.get("text") or ""
        if mcp_pull_text:
            pull_col1, pull_col2 = st.columns(2)
            with pull_col1:
                use_as_summary = st.button("Use as summary for assessment", use_container_width=True, key="mcp_raw_use_as_summary_btn")
            with pull_col2:
                use_as_transcript = st.button("Use as transcript for assessment", use_container_width=True, key="mcp_raw_use_as_transcript_btn")
            if use_as_summary or use_as_transcript:
                st.session_state.pop("granola_mcp_selected_meeting", None)
            if use_as_summary:
                st.session_state["mcp_pulled_summary"] = mcp_pull_text
            if use_as_transcript:
                st.session_state["mcp_pulled_transcript"] = _clean_mcp_transcript_text(mcp_pull_text)
            if use_as_summary or use_as_transcript:
                st.session_state["view"] = "review"
                st.rerun()


def render_add_source_view(provider: str, api_key: str, model: str) -> None:
    """The "add_source" view: the intake screen for picking where a transcript comes
    from - manual paste/upload on the left, Granola (MCP or REST API key) on the right.
    Both cards are always visible side by side; only the Granola card's internal state
    (not-connected / REST-connected / MCP-connected) branches.
    """
    if st.button("← Back to library", key="add_source_back_btn"):
        st.session_state["view"] = "library"
        st.rerun()
    st.markdown(
        _section_header_html("Your workspace", "Bring an interview to review", "Pick a source below - both are available in this intake area.", size="lg"),
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            f'<div style="font-family:{FONT_SERIF};font-weight:600;font-size:19px;color:{TEXT_PRIMARY};margin-bottom:2px;">Choose a source</div>'
            '<div class="pmic-subtitle" style="margin-bottom:16px;">Both options are available - pick whichever you have.</div>',
            unsafe_allow_html=True,
        )

        source_col_left, source_col_right = st.columns(2)

        with source_col_left:
            with st.container(border=True):
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">'
                    '<div style="display:flex;gap:10px;">'
                    f'<div style="width:34px;height:34px;border-radius:8px;background:{ACCENT_BLUE_BG};display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">✏️</div>'
                    '<div>'
                    f'<div style="font-family:{FONT_SANS};font-weight:700;font-size:14px;color:{TEXT_PRIMARY};">Manual transcript</div>'
                    f'<div style="font-family:{FONT_SANS};font-size:12.5px;color:{TEXT_SECONDARY};">Paste or upload a plain text file</div>'
                    "</div></div>"
                    + _chip_html("Available", "good")
                    + "</div>",
                    unsafe_allow_html=True,
                )

                with st.expander("Additional context (optional, but improves the assessment)"):
                    summary = st.text_area(
                        "Interview summary (e.g. Granola's AI-generated notes)",
                        height=120,
                        placeholder="Paste the meeting summary/notes here, if you have them separately from the raw transcript...",
                        key="manual_summary_area",
                    )
                    man_col1, man_col2 = st.columns(2)
                    with man_col1:
                        target_role = st.text_input("Target role", placeholder="e.g. Senior PM, Growth", key="manual_target_role")
                    with man_col2:
                        outcome = st.selectbox("Candidate-reported outcome", OUTCOME_OPTIONS, key="manual_outcome")
                    question_context = st.text_area(
                        "Question context",
                        height=80,
                        placeholder="e.g. 45-minute product sense round, panel of two interviewers...",
                        key="manual_question_context",
                    )
                    outcome_other = ""
                    if outcome == "Other (describe below)":
                        outcome_other = st.text_input("Describe the outcome", key="manual_outcome_other")

                transcript = st.text_area(
                    "Transcript",
                    height=220,
                    label_visibility="collapsed",
                    placeholder="Interviewer: Let's start with a product sense question...\nCandidate: Sure, so I'd first want to understand...",
                    key="manual_transcript_area",
                )
                upload = st.file_uploader("Upload a transcript (.txt)", type=["txt"], label_visibility="collapsed", key="manual_file_uploader")
                if upload:
                    transcript = upload.read().decode("utf-8")

                st.caption(f"{len(transcript)} characters · local only")

                analyze_clicked = st.button("Run analysis", type="primary", use_container_width=True, key="manual_run_btn")
                if analyze_clicked:
                    resolved_outcome = outcome_other.strip() if outcome == "Other (describe below)" and outcome_other.strip() else outcome
                    run_assessment_flow(provider, api_key, model, summary, transcript, target_role, question_context, resolved_outcome, "")
                    st.session_state["view"] = "report"
                    st.rerun()

        with source_col_right:
            with st.container(border=True):
                connected_rest = bool(st.session_state.get("granola_connected"))
                connected_mcp = bool(st.session_state.get("granola_mcp_tools"))
                pill_status, pill_text = ("good", "Connected") if (connected_rest or connected_mcp) else ("info", "Available")
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">'
                    '<div style="display:flex;gap:10px;">'
                    f'<div style="width:34px;height:34px;border-radius:8px;background:{ACCENT_BLUE_BG};display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">🎧</div>'
                    '<div>'
                    f'<div style="font-family:{FONT_SANS};font-weight:700;font-size:14px;color:{TEXT_PRIMARY};">Connect Granola</div>'
                    f'<div style="font-family:{FONT_SANS};font-size:12.5px;color:{TEXT_SECONDARY};">Sign in via MCP, or use an API key</div>'
                    "</div></div>"
                    + _chip_html(pill_text, pill_status)
                    + "</div>",
                    unsafe_allow_html=True,
                )

                if not connected_rest and not connected_mcp:
                    st.caption("Works on any Granola plan, including Basic - no API key needed.")
                    if st.button("🎧 Connect via MCP", type="primary", use_container_width=True, key="add_source_connect_mcp_btn"):
                        with st.spinner("Opening Granola in your browser - approve access there to continue (up to 3 minutes)..."):
                            try:
                                tools = granola_mcp_connect()
                            except GranolaAPIError as e:
                                st.error(str(e))
                            else:
                                st.session_state["granola_mcp_tools"] = tools
                                st.rerun()
                    with st.expander("Have a Granola API key instead?"):
                        granola_key_input = st.text_input(
                            "Granola API key",
                            type="password",
                            placeholder="grn_...",
                            help="Generate one in the Granola desktop app, under Settings → API access.",
                            key="add_source_granola_key_input",
                        )
                        if st.button("Connect", type="primary", key="granola_key_connect_btn"):
                            if not granola_key_input:
                                st.error("Enter your Granola API key first.")
                            else:
                                with st.spinner("Checking your key..."):
                                    try:
                                        granola_request(granola_key_input, "/notes", {"page_size": 1})
                                    except GranolaAPIError as e:
                                        st.error(str(e))
                                    else:
                                        st.session_state["granola_connected"] = True
                                        st.session_state["granola_key"] = granola_key_input
                                        for k in ["granola_notes", "granola_cursor", "granola_has_more", "granola_folders", "granola_folder_id", "granola_selected_note"]:
                                            st.session_state.pop(k, None)
                                        st.rerun()

                elif connected_rest:
                    granola_key = st.session_state["granola_key"]
                    if st.button("Disconnect", key="granola_key_disconnect"):
                        for k in ["granola_connected", "granola_key", "granola_notes", "granola_cursor", "granola_has_more", "granola_folders", "granola_folder_id", "granola_selected_note"]:
                            st.session_state.pop(k, None)
                        st.rerun()

                    if "granola_folders" not in st.session_state:
                        try:
                            st.session_state["granola_folders"] = granola_list_all_folders(granola_key)
                        except GranolaAPIError as e:
                            st.session_state["granola_folders"] = []
                            st.warning(f"Couldn't load folders: {e}")

                    folder_options = {"All folders": None}
                    for f in st.session_state["granola_folders"]:
                        folder_options[f["name"]] = f["id"]
                    folder_label = st.selectbox("Folder", list(folder_options.keys()), key="add_source_folder_select")
                    selected_folder_id = folder_options[folder_label]

                    if "granola_notes" not in st.session_state or st.session_state.get("granola_folder_id") != selected_folder_id:
                        try:
                            notes, has_more, cursor = granola_list_notes(granola_key, folder_id=selected_folder_id, page_size=20)
                        except GranolaAPIError as e:
                            st.error(str(e))
                            notes, has_more, cursor = [], False, None
                        st.session_state["granola_notes"] = notes
                        st.session_state["granola_has_more"] = has_more
                        st.session_state["granola_cursor"] = cursor
                        st.session_state["granola_folder_id"] = selected_folder_id

                    search = st.text_input("Filter loaded interviews by title", placeholder="Search...", key="add_source_notes_search")
                    notes = st.session_state["granola_notes"]
                    if search:
                        notes = [n for n in notes if search.lower() in (n.get("title") or "").lower()]

                    if not notes:
                        st.info("No interviews found. Only meetings with a generated Granola summary appear here.")

                    for note in notes:
                        title = note.get("title") or "Untitled interview"
                        created = (note.get("created_at") or "")[:10]
                        row = st.columns([5, 2])
                        with row[0]:
                            st.markdown(f"**{title}**")
                            st.caption(created)
                        with row[1]:
                            st.write("")
                            if st.button("Select", key=f"select_{note['id']}", use_container_width=True):
                                with st.spinner("Fetching interview details..."):
                                    try:
                                        st.session_state["granola_selected_note"] = granola_get_note(granola_key, note["id"])
                                    except GranolaAPIError as e:
                                        st.error(str(e))
                                    else:
                                        st.session_state["view"] = "review"
                                        st.rerun()

                    if st.session_state.get("granola_has_more"):
                        if st.button("Load more interviews", key="add_source_load_more_btn"):
                            try:
                                more_notes, has_more, cursor = granola_list_notes(
                                    granola_key, folder_id=selected_folder_id, cursor=st.session_state["granola_cursor"], page_size=20
                                )
                                st.session_state["granola_notes"] = st.session_state["granola_notes"] + more_notes
                                st.session_state["granola_has_more"] = has_more
                                st.session_state["granola_cursor"] = cursor
                                st.rerun()
                            except GranolaAPIError as e:
                                st.error(str(e))

                elif connected_mcp:
                    MCP_SESSION_KEYS = [
                        "granola_mcp_tools", "granola_mcp_tool_schemas", "granola_mcp_tokens", "granola_mcp_client_info",
                        "granola_mcp_last_result", "granola_mcp_meetings", "granola_mcp_meetings_found", "granola_mcp_meetings_error",
                        "granola_mcp_selected_meeting", "mcp_pulled_summary", "mcp_pulled_transcript",
                    ]

                    tool_names = st.session_state["granola_mcp_tools"]
                    tool_schemas = st.session_state.get("granola_mcp_tool_schemas", {})

                    top_left, top_right = st.columns([3, 2])
                    with top_left:
                        st.caption(f"{len(tool_names)} tools available.")
                    with top_right:
                        if st.button("Disconnect", key="granola_mcp_disconnect", use_container_width=True):
                            for k in MCP_SESSION_KEYS:
                                st.session_state.pop(k, None)
                            st.rerun()

                    # Auto-load the call list once per connection - this is what makes MCP feel
                    # like "one connected experience" instead of a manual tool console to drive.
                    if "list_meetings" in tool_names and "granola_mcp_meetings" not in st.session_state:
                        with st.spinner("Loading your recent calls..."):
                            try:
                                result = granola_mcp_call_tool("list_meetings", {})
                            except GranolaAPIError as e:
                                st.session_state["granola_mcp_meetings_error"] = str(e)
                                st.session_state["granola_mcp_meetings"] = []
                                st.session_state["granola_mcp_meetings_found"] = False
                            else:
                                if result["is_error"]:
                                    st.session_state["granola_mcp_meetings_error"] = result["text"] or "list_meetings returned an error."
                                    st.session_state["granola_mcp_meetings"] = []
                                    st.session_state["granola_mcp_meetings_found"] = False
                                else:
                                    meetings = _find_meeting_list(result)
                                    st.session_state["granola_mcp_meetings"] = meetings or []
                                    st.session_state["granola_mcp_meetings_found"] = meetings is not None

                    meetings_found = st.session_state.get("granola_mcp_meetings_found", False)

                    if meetings_found:
                        meetings = st.session_state.get("granola_mcp_meetings", [])
                        search = st.text_input("Filter your calls by title", placeholder="Search...", key="mcp_meeting_search")
                        if st.button("🔄 Refresh", key="mcp_refresh_meetings"):
                            for k in ["granola_mcp_meetings", "granola_mcp_meetings_found", "granola_mcp_meetings_error"]:
                                st.session_state.pop(k, None)
                            st.rerun()

                        visible = [m for m in meetings if search.lower() in _meeting_title(m).lower()] if search else meetings
                        if not meetings:
                            st.info("No calls found via MCP yet.")
                        elif not visible:
                            st.info("No calls match your search.")
                        for m in visible:
                            mid = _meeting_id(m)
                            row = st.columns([5, 2])
                            with row[0]:
                                st.markdown(f"**{_meeting_title(m)}**")
                                st.caption(_meeting_date(m))
                            with row[1]:
                                st.write("")
                                if st.button("Select", key=f"mcp_select_{mid}", use_container_width=True):
                                    id_arg = _tool_id_arg_name(tool_schemas.get("get_meeting_transcript", {}))
                                    with st.spinner("Fetching transcript..."):
                                        try:
                                            t_result = granola_mcp_call_tool("get_meeting_transcript", {id_arg: mid})
                                        except GranolaAPIError as e:
                                            st.error(str(e))
                                        else:
                                            if t_result["is_error"]:
                                                st.error(t_result["text"] or "Couldn't fetch the transcript for this call.")
                                            else:
                                                st.session_state["granola_mcp_selected_meeting"] = m
                                                st.session_state["mcp_pulled_summary"] = _meeting_summary(m)
                                                st.session_state["mcp_pulled_transcript"] = _clean_mcp_transcript_text(t_result.get("text") or "")
                                                st.session_state["view"] = "review"
                                                st.rerun()

                        with st.expander("Advanced: raw tool console"):
                            _render_mcp_raw_console(tool_names, tool_schemas)
                    else:
                        if st.session_state.get("granola_mcp_meetings_error"):
                            st.warning(f"Couldn't load your call list: {st.session_state['granola_mcp_meetings_error']}")
                        else:
                            st.info(
                                "Couldn't build a browsable call list from this server's response - Granola "
                                "hasn't published exact MCP output schemas for third-party clients, so this "
                                "falls back to the raw tool console below rather than guessing at a shape "
                                "that might be wrong."
                            )
                            _render_mcp_raw_console(tool_names, tool_schemas)
