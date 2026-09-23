"""
pm_coach - internal package for the AI PM Interview Coach Streamlit app.

The app is started via `streamlit run pm_interview_coach.py` (one directory up from this
package) - that file stays the entry point (page config, sidebar, view dispatch) and imports
everything else from here. This docstring is the map: what each module owns, and the rough
dependency order (each module only imports from ones listed above it).

    config.py            Paths, Granola endpoints, provider/model registry, question-type and
                          outcome option lists. _remembered_api_key() (secrets.toml/env lookup).

    prompts.py            SYSTEM_PROMPT (the full assessment rubric) and SUMMARY_SYSTEM_PROMPT
                          (cross-session recurring-issues prompt). Prompt text only, no logic -
                          edit here, never regenerate by hand.

    llm_client.py         call_llm() - the only place that calls Claude or OpenAI. Normalizes
                          both providers' responses to (text, truncated).

    granola_rest.py       Granola's key-based REST API client + GranolaAPIError (the shared
                          exception both Granola clients raise).

    granola_mcp.py        Granola's MCP/OAuth connection (no-key sign-in, works on any plan) +
                          defensive parsing of its real (undocumented, reverse-engineered)
                          list_meetings/get_meeting_transcript response shapes.

    signals.py             compute_conversation_signals() - filler words, speaking share, etc.,
                          counted deterministically from transcript text, never estimated by
                          the model.

    report_parsing.py     Turns the model's raw report_md into structured data: build the
                          request content, extract markdown sections, parse/repair/strip the
                          leading JSON summary block. _repair_json_quotes is a hard-won fixup
                          for a real recurring model mistake - see its own docstring first.

    log_store.py           Reads/writes progress_log.md (gitignored, local-only): append a
                          session, parse past entries into cards, derive a session label from
                          a report's own headline when the caller didn't already have one.

    design_tokens.py       Every color/font constant (read off the reference app's compiled
                          CSS) + _inject_design_system(), which injects them as global CSS.

    ui_components.py       Reusable HTML-snippet builders (chips, cards, bars, section
                          headers). Pure string builders - no st.* widget calls live here.

    dashboard.py            render_report_dashboard() / render_last_report() - turns one
                          assessment's JSON summary + markdown into the full visual report.

    assessment_flow.py     run_assessment_flow() - the one controller all three "Run analysis"
                          buttons call: validate -> call the model -> log -> stash into
                          session_state. Exactly one copy of this must run regardless of which
                          source (manual/REST/MCP) triggered it.

    view_assessment.py     render_report_view() + render_review_view() - the "report" and
                          "review" `st.session_state["view"]` states (see one assessment
                          before/after running it).

    view_library.py        render_library_view() + render_past_detail_view() - the "library"
                          (home/default) and "past_detail" `view` states (the session log).

    view_add_source.py     render_add_source_view() - the "add_source" `view` state (pick a
                          transcript source: manual paste/upload, or Granola via MCP/REST key).
                          Also owns _render_mcp_raw_console(), the manual tool-console fallback.

To find something: HTML/markup bugs -> ui_components.py or dashboard.py. A Granola API/shape
bug -> granola_rest.py (key-based) or granola_mcp.py (OAuth + meeting/transcript parsing). A
prompt/rubric change -> prompts.py only. A navigation/button bug -> whichever view_*.py owns
that `view` state, per the list above. progress_log.md format -> log_store.py.
"""
