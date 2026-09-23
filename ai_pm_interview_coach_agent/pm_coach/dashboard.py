"""
Renders the full visual assessment report: render_report_dashboard() turns the model's JSON
summary block + markdown body into the scannable dashboard (header, rating cards, why-depth
bar, conversation signals, major issues, per-question expanders); degrades gracefully to the
plain markdown report when the JSON summary is missing/unparseable, so a malformed response
never hides the report entirely. render_last_report() is the thin wrapper the "report" view
calls - renders the dashboard for st.session_state["last_report"] plus its download button.
"""
import html
from datetime import datetime

import streamlit as st

from .design_tokens import FONT_SANS, TEXT_PRIMARY
from .report_parsing import _extract_section, _extract_json_summary, _split_question_sections, _strip_json_block
from .ui_components import (
    _callout_box_html,
    _insight_card_html,
    _landed_card_html,
    _major_issue_html,
    _meta_row_html,
    _opening_assessment_html,
    _quote_card_html,
    _rating_card_v2_html,
    _section_header_html,
    _sentiment_item_html,
    _signal_stat_html,
    _why_depth_bar_html,
)


def render_report_dashboard(report_md: str, signals: dict | None = None, truncated: bool = False, generated_at=None) -> None:
    summary, parse_error = _extract_json_summary(report_md)
    if not summary:
        if truncated:
            st.warning("The model's response hit its length limit before finishing, so the visual summary couldn't be built - showing the full (likely incomplete) markdown instead. Try running the assessment again.")
        elif parse_error:
            st.caption(f"Couldn't build the visual summary for this report ({parse_error}) - showing the full markdown instead.")
        else:
            st.caption("Couldn't build the visual summary for this report - showing the full markdown instead.")
        st.markdown(report_md)
        return

    body_md = _strip_json_block(report_md)
    signals = signals or {}
    ratings = summary.get("ratings") or []
    date_str = (generated_at or datetime.now()).strftime("%d %b %Y").upper()

    # --- Header ---
    headline = summary.get("headline") or "Interview assessment"
    st.markdown(
        f'<div class="pmic-eyebrow">DEBRIEF REPORT · {html.escape(date_str)}</div>'
        f'<div class="pmic-h1">{html.escape(headline)}</div>'
        f'<div class="pmic-subtitle">A focused read of what happened, evidence attached to every claim.</div>',
        unsafe_allow_html=True,
    )

    outcome = summary.get("reported_outcome")
    meta_items = [
        ("Question types", summary.get("question_types") or "Not provided"),
        ("Source", summary.get("source_quality") or "Not provided"),
        ("Outcome (candidate-reported)", outcome if outcome and outcome != "Not provided" else "Not provided"),
        ("Speaker coverage", "Candidate + interviewer turns" if signals.get("speakers_identified") else "Not identified in transcript"),
    ]
    st.markdown(_meta_row_html(meta_items), unsafe_allow_html=True)
    if summary.get("caveats"):
        st.caption(summary["caveats"])

    # --- Opening assessment: the candidate's intro and first substantive answer, on its own ---
    opening = summary.get("opening_assessment") or {}
    if opening.get("summary"):
        st.markdown(
            _opening_assessment_html(opening["summary"], opening.get("evidence") or "", opening.get("note") or ""),
            unsafe_allow_html=True,
        )

    if summary.get("overall_read"):
        st.markdown(_quote_card_html("In two sentences", summary["overall_read"]), unsafe_allow_html=True)

    # --- Answer assessment: five independent, evidence-backed ratings ---
    st.markdown(_section_header_html("Provisional rubric", "Five lenses, not a verdict", "Whole-number ratings anchored to the available transcript. Not a ranking against other candidates."), unsafe_allow_html=True)
    cards_html = '<div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px;">'
    for r in ratings:
        cards_html += _rating_card_v2_html(r.get("name") or r.get("key") or "Dimension", r.get("value"), r.get("note") or "", r.get("evidence") or "")
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)
    st.caption("1 Substantial gap · 2 Developing · 3 Effective · 4 Strong · 5 Excellent")

    why_depth = summary.get("why_depth") or {}
    stated = why_depth.get("stated") or 0
    explained = why_depth.get("explained") or 0
    justified = why_depth.get("justified") or 0
    why_bar = _why_depth_bar_html(stated, explained, justified, why_depth.get("gap") or "")
    if why_bar:
        st.markdown(f'<div style="font-family:{FONT_SANS};font-weight:700;font-size:14px;color:{TEXT_PRIMARY};margin:18px 0 4px;">Reasoning depth</div>', unsafe_allow_html=True)
        st.caption("How well-grounded were the candidate's choices - stated outright, explained with a reason, or justified against evidence/tradeoffs?")
        st.markdown(why_bar, unsafe_allow_html=True)

    # --- Conversation signals: measured from the transcript's own text, never estimated ---
    stat_items = []
    if signals.get("filler_total") is not None:
        stat_items.append(("Filler words", str(signals["filler_total"])))
    if "speaking_share_pct" in signals:
        stat_items.append(("Candidate speaking share", f"{signals['speaking_share_pct']}%"))
    if "longest_answer_words" in signals:
        stat_items.append(("Longest answer", f"{signals['longest_answer_words']} words"))
    if signals.get("speakers_identified") and "candidate_questions" in signals:
        stat_items.append(("Questions asked by candidate", str(signals["candidate_questions"])))
    elif signals.get("questions_total") is not None:
        stat_items.append(("Questions asked (either side)", str(signals["questions_total"])))
    if stat_items:
        st.markdown(_section_header_html("Measured, not estimated", "Conversation signals", "Counted directly from the transcript's own text."), unsafe_allow_html=True)
        st.markdown(
            '<div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:6px;">' + "".join(_signal_stat_html(l, v) for l, v in stat_items) + "</div>",
            unsafe_allow_html=True,
        )
        if not signals.get("speakers_identified"):
            st.caption("Couldn't identify separate speakers in this transcript, so speaking share and longest answer aren't available.")
        if signals.get("filler_breakdown"):
            top = sorted(signals["filler_breakdown"].items(), key=lambda kv: -kv[1])[:5]
            st.caption("Most common: " + ", ".join(f'“{w}” ({c})' for w, c in top))

    # --- Two-column: what held up (evidence) / three useful tensions (at a glance) ---
    what_worked = summary.get("what_worked") or []
    major_issues = summary.get("major_issues") or []
    practice_plan = summary.get("practice_plan") or []
    not_assessed = [r for r in ratings if r.get("value") is None]

    if what_worked or major_issues or why_depth.get("gap") or not_assessed:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(_section_header_html("Read the evidence", "What held up", "Claims below point back to the transcript, not inferred intent."), unsafe_allow_html=True)
            if what_worked:
                strengths_html = "<ul style='margin:0;padding-left:18px;'>" + "".join(
                    f"<li style='margin-bottom:6px;'><strong>{html.escape(w.get('title') or '')}</strong> — {html.escape(w.get('description') or '')}</li>"
                    for w in what_worked
                ) + "</ul>"
                st.markdown(_callout_box_html("✅", "Strengths to keep", strengths_html, "good"), unsafe_allow_html=True)
            next_action = (major_issues[0].get("next_time") if major_issues else None) or (practice_plan[0] if practice_plan else None)
            if next_action:
                st.markdown("")
                st.markdown(_callout_box_html("💡", "One action to practise next", html.escape(next_action), "warning"), unsafe_allow_html=True)
        with col_right:
            st.markdown(_section_header_html("At a glance", "Useful tensions", "Not a verdict - the specific threads worth pulling on next."), unsafe_allow_html=True)
            tensions_html = ""
            if why_depth.get("gap"):
                tensions_html += _insight_card_html("☑️", "Reasoning gap", why_depth["gap"], "warning")
            if major_issues:
                tensions_html += _insight_card_html("🎯", major_issues[0].get("title") or "Top issue", major_issues[0].get("evidence") or "", "warning")
            if not_assessed:
                dim = not_assessed[0]
                tensions_html += _insight_card_html("🎧", f"{dim.get('name') or 'Dimension'} not assessed", dim.get("evidence") or "", "muted")
            if tensions_html:
                st.markdown(tensions_html, unsafe_allow_html=True)

    # --- Interviewer response: outcome signals, never folded into a skill rating ---
    how_it_landed = summary.get("how_it_landed") or []
    expressed_sentiment = summary.get("expressed_sentiment") or []
    if how_it_landed or expressed_sentiment:
        st.markdown(_section_header_html("Interviewer response", "What the other side signalled", "Observations from transcript excerpts, not emotional interpretations."), unsafe_allow_html=True)
        if how_it_landed:
            landed_html = '<div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:10px;">' + "".join(
                _landed_card_html(item.get("classification") or "", item.get("excerpt") or "", item.get("refers_to") or "")
                for item in how_it_landed
            ) + "</div>"
            st.markdown(landed_html, unsafe_allow_html=True)
        if expressed_sentiment:
            st.caption("Candidate-expressed sentiment")
            sentiment_html = "".join(
                _sentiment_item_html(item.get("sentiment") or "", item.get("target") or "", item.get("evidence") or "")
                for item in expressed_sentiment
            )
            st.markdown(sentiment_html, unsafe_allow_html=True)

    # --- Major issues and practice: ranked by impact, each tied to a concrete next action ---
    if major_issues:
        st.markdown(_section_header_html("Major issues and practice", "Ranked by impact on the answer", ""), unsafe_allow_html=True)
        issues_html = '<div style="display:flex;flex-direction:column;gap:10px;margin-bottom:12px;">' + "".join(
            _major_issue_html(i + 1, issue.get("title") or f"Issue {i + 1}", issue.get("evidence") or "", issue.get("next_time") or "")
            for i, issue in enumerate(major_issues)
        ) + "</div>"
        st.markdown(issues_html, unsafe_allow_html=True)

    if practice_plan:
        st.markdown(f'<div style="font-family:{FONT_SANS};font-weight:700;font-size:14px;color:{TEXT_PRIMARY};margin:6px 0 6px;">Practice plan</div>', unsafe_allow_html=True)
        for item in practice_plan:
            st.markdown(f"- {html.escape(item)}")

    # --- Your answers, unpacked: per-question rows instead of one long dump ---
    questions_meta = summary.get("questions") or []
    question_bodies = _split_question_sections(body_md)
    if questions_meta and question_bodies:
        st.markdown(_section_header_html("Walk the exchange", "Question-by-question review", "Open a question to see the answer, the evidence it supports, and the next-level prompt."), unsafe_allow_html=True)
        for q in questions_meta:
            try:
                n = int(q.get("n"))
            except (TypeError, ValueError):
                continue
            qtext = q.get("question") or f"Question {n}"
            category = q.get("category") or ""
            body = question_bodies.get(n, "")
            label = f"{n:02d}  {qtext}" + (f"  ·  {category}" if category else "")
            with st.expander(label):
                st.markdown(body or "Not available.")
    else:
        qa_md = _extract_section(body_md, "## 4. Question-by-Question Assessment", "## 5. How The Answers Landed")
        if qa_md:
            with st.expander("📋 See the full question-by-question analysis"):
                st.markdown(qa_md)


def render_last_report(key_suffix: str) -> None:
    if "last_report" in st.session_state:
        st.divider()
        render_report_dashboard(
            st.session_state["last_report"],
            st.session_state.get("last_signals", {}),
            st.session_state.get("last_report_truncated", False),
            st.session_state.get("last_report_time"),
        )
        st.download_button(
            "Download report (.md)",
            data=st.session_state["last_report"],
            file_name=f"pm-interview-assessment-{datetime.now().strftime('%Y%m%d-%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"download_{key_suffix}",
        )
