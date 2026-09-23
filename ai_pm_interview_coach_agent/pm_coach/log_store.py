"""
Reads and writes progress_log.md, the local (gitignored) running log of past sessions:
append_to_log after each assessment, read_log/_parse_log_entries to power the library view's
cards. Each entry embeds a small ```logmeta fenced JSON block (headline, question types,
major-issue count, etc.) right after its header so the library can render a card without
re-parsing the full markdown body; _parse_log_entries falls back to the entry's own header
title for older entries written before that block existed, rather than losing them.
_derive_session_label pulls a label from the report's own headline when the caller didn't
already have one (e.g. manual paste has no note/meeting title to borrow).
"""
import json
import os
import re
from datetime import datetime

from .config import LOG_PATH
from .report_parsing import _extract_json_summary, _extract_section


def append_to_log(candidate: str, report_md: str) -> None:
    summary, _ = _extract_json_summary(report_md)
    meta = {
        "headline": (summary or {}).get("headline") or candidate or "Untitled session",
        "overall_read": (summary or {}).get("overall_read") or "",
        "question_types": (summary or {}).get("question_types") or "Not provided",
        "source_quality": (summary or {}).get("source_quality") or "Not provided",
        "reported_outcome": (summary or {}).get("reported_outcome") or "Not provided",
        "major_issues_count": len((summary or {}).get("major_issues") or []),
    }
    # A distinct fence label (not "json") so this block is never mistaken for the report's own
    # JSON summary if _extract_json_summary is ever pointed at log content.
    entry_lines = [
        f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} - {candidate or 'Untitled session'}\n",
        "```logmeta\n" + json.dumps(meta) + "\n```\n",
    ]

    snapshot_and_dashboard = _extract_section(report_md, "## 1. Snapshot", "## 4. Question-by-Question Assessment")
    major_issues = _extract_section(report_md, "## 9. MAJOR ISSUES FOUND", None)

    if snapshot_and_dashboard:
        entry_lines.append(snapshot_and_dashboard + "\n")
    if major_issues:
        entry_lines.append(major_issues + "\n")
    if not snapshot_and_dashboard and not major_issues:
        entry_lines.append(report_md.strip() + "\n")

    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w") as f:
            f.write("# Interview Progress Log\n\nTracks recurring patterns across coaching sessions so prep actually improves over time.\n")

    with open(LOG_PATH, "a") as f:
        f.write("\n".join(entry_lines))


def read_log() -> str:
    if not os.path.exists(LOG_PATH):
        return ""
    with open(LOG_PATH) as f:
        return f.read()


def _parse_log_entries(log_content: str) -> list:
    """Splits the log into per-session entries, pulling the structured ```logmeta block out
    when present so the Progress Log tab can render cards instead of a raw markdown dump.
    Entries written before this format existed (no meta block) still show up, just without
    the card's richer fields - never lose old sessions over a format change."""
    entries = []
    matches = list(re.finditer(r"^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) - (.*)$", log_content, re.MULTILINE))
    for i, m in enumerate(matches):
        date_str, header_title = m.group(1), m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(log_content)
        body = log_content[start:end].strip()
        meta = {}
        meta_match = re.match(r"```logmeta\s*(\{.*?\})\s*```", body, re.DOTALL)
        if meta_match:
            try:
                meta = json.loads(meta_match.group(1))
            except json.JSONDecodeError:
                meta = {}
            body = body[meta_match.end():].strip()
        entries.append({
            "date": date_str,
            "headline": meta.get("headline") or header_title,
            "overall_read": meta.get("overall_read") or "",
            "question_types": meta.get("question_types") or "Not provided",
            "source_quality": meta.get("source_quality") or "Not provided",
            "reported_outcome": meta.get("reported_outcome") or "Not provided",
            "major_issues_count": meta.get("major_issues_count"),
            "body": body,
        })
    entries.reverse()
    return entries
def _derive_session_label(report_md: str) -> str:
    """A session label the caller didn't already have (e.g. manual paste, which has no note/
    meeting title to borrow) - pulled from the report's own headline so nothing needs typing."""
    summary, _ = _extract_json_summary(report_md)
    if summary and summary.get("headline"):
        return summary["headline"]
    return f"Session - {datetime.now().strftime('%d %b %Y, %H:%M')}"
