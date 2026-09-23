"""
Reusable HTML-snippet builder functions shared by the dashboard and the view modules - section
headers, chips/pills, quote cards, rating cards, the why-depth bar, the library's session
cards, etc. Every function here returns an HTML string for st.markdown(..., unsafe_allow_html
=True); none of them call Streamlit widget functions directly (that's the view/dashboard
modules' job) - keeping that split means these are trivially reusable across views.
"""
import html

from .design_tokens import (
    ACCENT_BLUE_BG,
    CARD_BG,
    CARD_BORDER,
    CHIP_BG,
    CHIP_FG,
    FONT_SANS,
    FONT_SERIF,
    RATING_ACCENT,
    STATUS_COLORS,
    SURFACE_MUTED,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from .report_parsing import _numeric_status


def _meta_row_plain_html(items: list) -> str:
    cols = []
    for label, value in items:
        cols.append(
            '<div style="flex:1;min-width:120px;">'
            f'<div style="font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;">{html.escape(label)}</div>'
            f'<div style="font-family:{FONT_SANS};font-size:13.5px;color:{TEXT_PRIMARY};">{html.escape(value) if value else "—"}</div>'
            "</div>"
        )
    return '<div style="display:flex;gap:24px;flex-wrap:wrap;">' + "".join(cols) + "</div>"


def _log_entry_card_html(entry: dict) -> str:
    issues_n = entry.get("major_issues_count")
    if isinstance(issues_n, int):
        pill_text = f"{issues_n} issue{'s' if issues_n != 1 else ''} found" if issues_n > 0 else "No major issues"
        pill_status = "warning" if issues_n > 0 else "good"
    else:
        pill_text, pill_status = "Logged", "muted"
    desc_html = (
        f'<div style="font-family:{FONT_SANS};font-size:13.5px;color:{TEXT_SECONDARY};line-height:1.5;margin-top:8px;">{html.escape(entry["overall_read"])}</div>'
        if entry["overall_read"] else ""
    )
    return (
        f'<div style="background:{CARD_BG};border:{CARD_BORDER};border-radius:14px;padding:20px 22px;">'
        '<div style="display:flex;gap:12px;">'
        f'<div style="width:34px;height:34px;border-radius:8px;background:{ACCENT_BLUE_BG};display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">📄</div>'
        '<div style="flex:1;">'
        f'{_chip_html(pill_text, pill_status)} <span style="font-family:{FONT_SANS};font-size:12px;color:{TEXT_MUTED};margin-left:6px;">{html.escape(entry["date"])}</span>'
        f'<div style="font-family:{FONT_SERIF};font-weight:600;font-size:18px;color:{TEXT_PRIMARY};margin-top:8px;">{html.escape(entry["headline"])}</div>'
        f"{desc_html}"
        "</div></div>"
        '<hr style="border:none;border-top:1px solid #eee;margin:16px 0;">'
        + _meta_row_plain_html([
            ("Question types", entry["question_types"]),
            ("Source", entry["source_quality"]),
            ("Outcome", entry["reported_outcome"]),
        ])
        + "</div>"
    )


def _section_header_html(eyebrow: str, title: str, subtitle: str = "", size: str = "md") -> str:
    """size="lg" is for a page's own title (library, add a source) - .pmic-h1, the same scale
    as the report headline. Internal dashboard section dividers stay "md" (.pmic-h2, smaller)
    so they read as subordinate to the page title, not competing with it."""
    subtitle_html = f'<div class="pmic-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    title_class = "pmic-h1" if size == "lg" else "pmic-h2"
    return f'<div class="pmic-eyebrow">{html.escape(eyebrow)}</div><div class="{title_class}">{html.escape(title)}</div>{subtitle_html}'


def _review_card_header_html(title: str, source_label: str) -> str:
    """Same icon+title/subtitle+pill header pattern as the 'Choose a source' cards, so the
    review screen reads as a continuation of that step, not a different, unstyled page."""
    return (
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">'
        '<div style="display:flex;gap:10px;">'
        f'<div style="width:34px;height:34px;border-radius:8px;background:{ACCENT_BLUE_BG};display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">📄</div>'
        '<div>'
        f'<div style="font-family:{FONT_SERIF};font-weight:600;font-size:17px;color:{TEXT_PRIMARY};">{html.escape(title)}</div>'
        f'<div style="font-family:{FONT_SANS};font-size:12.5px;color:{TEXT_SECONDARY};">{html.escape(source_label)}</div>'
        "</div></div>"
        + _chip_html("Ready to run", "info")
        + "</div>"
    )


def _meta_row_html(items: list) -> str:
    cols = []
    for label, value in items:
        cols.append(
            '<div style="flex:1;min-width:150px;">'
            f'<div style="font-family:{FONT_SANS};font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;">{html.escape(label)}</div>'
            f'<div style="font-family:{FONT_SANS};font-size:14px;color:{TEXT_PRIMARY};font-weight:500;">{html.escape(value) if value else "—"}</div>'
            "</div>"
        )
    return (
        f'<div style="display:flex;gap:24px;flex-wrap:wrap;background:{CARD_BG};border:{CARD_BORDER};border-radius:14px;padding:18px 22px;margin:14px 0;">'
        + "".join(cols) + "</div>"
    )


def _quote_card_html(eyebrow: str, text: str) -> str:
    return (
        f'<div style="background:{CARD_BG};border:{CARD_BORDER};border-radius:14px;padding:22px 26px;margin:0 0 20px;">'
        f'<div class="pmic-eyebrow">❝ {html.escape(eyebrow)}</div>'
        f'<div style="font-family:{FONT_SERIF};font-weight:600;font-size:19px;line-height:1.5;color:{TEXT_PRIMARY};">{html.escape(text)}</div>'
        "</div>"
    )


def _rating_card_v2_html(name: str, value, note: str, evidence: str) -> str:
    status = _numeric_status(value)
    accent = RATING_ACCENT[status]
    if value is None:
        value_html = f'<div style="font-family:{FONT_SANS};font-weight:700;font-size:15px;color:{accent};margin:10px 0 8px;">Not assessed</div>'
    else:
        value_html = f'<div style="font-family:{FONT_SERIF};font-weight:700;font-size:30px;color:{accent};line-height:1;margin:10px 0 8px;">{int(value)}</div>'
    note_html = f'<div style="font-size:12px;color:{TEXT_MUTED};margin-bottom:4px;">{html.escape(note)}</div>' if (value is not None and note) else ""
    return (
        f'<div style="flex:1;min-width:180px;background:{CARD_BG};border:{CARD_BORDER};border-top:3px solid {accent};border-radius:12px;padding:16px 18px;">'
        f'<div style="font-family:{FONT_SANS};font-size:13px;font-weight:600;color:{TEXT_PRIMARY};">{html.escape(name)}</div>'
        f"{value_html}{note_html}"
        f'<div style="font-size:12.5px;color:{TEXT_SECONDARY};line-height:1.5;">{html.escape(evidence)}</div>'
        "</div>"
    )


def _callout_box_html(icon: str, title: str, body_html: str, tone: str) -> str:
    return (
        f'<div style="background:{CHIP_BG[tone]};border-radius:14px;padding:20px 22px;height:100%;box-sizing:border-box;">'
        f'<div style="display:flex;align-items:center;gap:8px;font-weight:700;color:{CHIP_FG[tone]};font-size:14px;margin-bottom:10px;">{icon} {html.escape(title)}</div>'
        f'<div style="font-size:13.5px;color:{TEXT_PRIMARY};line-height:1.65;">{body_html}</div>'
        "</div>"
    )


def _insight_card_html(icon: str, title: str, description: str, tone: str) -> str:
    return (
        f'<div style="background:{CHIP_BG[tone]};border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
        f'<div style="font-size:13px;margin-bottom:4px;">{icon}</div>'
        f'<div style="font-weight:700;font-size:14px;color:{TEXT_PRIMARY};margin-bottom:3px;">{html.escape(title)}</div>'
        f'<div style="font-size:12.5px;color:{TEXT_SECONDARY};line-height:1.5;">{html.escape(description)}</div>'
        "</div>"
    )
def _chip_html(text: str, status: str) -> str:
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;'
        f'font-weight:600;background:{CHIP_BG[status]};color:{CHIP_FG[status]};white-space:nowrap;">'
        f"{html.escape(text)}</span>"
    )


def _opening_assessment_html(summary_text: str, evidence: str, note: str) -> str:
    evidence_html = f'<div style="font-size:13px;color:{TEXT_SECONDARY};line-height:1.5;margin-top:4px;">{html.escape(evidence)}</div>' if evidence else ""
    note_html = f'<div style="font-size:12px;color:{TEXT_MUTED};margin-top:6px;">{html.escape(note)}</div>' if note else ""
    return (
        f'<div style="background:{SURFACE_MUTED};border-radius:12px;padding:16px 20px;margin:4px 0 20px;">'
        f'<div class="pmic-eyebrow" style="margin-bottom:4px;">Opening assessment</div>'
        f'<div style="font-size:14px;color:{TEXT_SECONDARY};line-height:1.5;">{html.escape(summary_text)}</div>'
        f"{evidence_html}{note_html}</div>"
    )


LANDED_STATUS = {
    "explicit positive feedback": "good",
    "explicit concern or correction": "critical",
    "request for clarification": "info",
    "further exploration": "info",
    "neutral acknowledgment": "muted",
    "unclear": "muted",
}


def _landed_card_html(classification: str, excerpt: str, refers_to: str) -> str:
    status = LANDED_STATUS.get((classification or "").strip().lower(), "muted")
    chip = _chip_html(classification or "Unclear", status)
    refers_html = f'<div style="font-size:12px;color:{TEXT_MUTED};margin-top:8px;">{html.escape(refers_to)}</div>' if refers_to else ""
    quote_html = (
        f'<div style="font-family:{FONT_SERIF};font-weight:600;font-size:16px;color:{TEXT_PRIMARY};line-height:1.4;margin-top:10px;">“{html.escape(excerpt)}”</div>'
        if excerpt else ""
    )
    return (
        f'<div style="flex:1;min-width:220px;background:{CARD_BG};border:{CARD_BORDER};border-radius:12px;padding:16px 18px;">'
        f"{chip}{quote_html}{refers_html}</div>"
    )


def _sentiment_item_html(sentiment: str, target: str, evidence: str) -> str:
    label = (sentiment or "").capitalize() or "Sentiment"
    target_html = f' <span style="font-size:12px;color:{TEXT_MUTED};">· about {html.escape(target)}</span>' if target else ""
    evidence_html = f'<div style="font-size:13px;color:{TEXT_SECONDARY};margin-top:4px;">{html.escape(evidence)}</div>' if evidence else ""
    return (
        '<div style="padding:10px 0;border-top:1px solid #eee;">'
        f'<span style="font-size:13px;font-weight:600;color:{TEXT_PRIMARY};">{html.escape(label)}</span>{target_html}'
        f"{evidence_html}</div>"
    )


def _why_depth_bar_html(stated: int, explained: int, justified: int, gap: str) -> str:
    total = stated + explained + justified
    if total <= 0:
        return ""

    def seg(count: int, color: str) -> str:
        pct = count / total * 100
        return f'<div style="height:100%;width:{pct:.1f}%;background:{color};"></div>' if count > 0 else ""

    bar = (
        '<div style="display:flex;height:14px;border-radius:7px;overflow:hidden;gap:2px;background:#f2f1ee;">'
        + seg(stated, STATUS_COLORS["critical"])
        + seg(explained, STATUS_COLORS["warning"])
        + seg(justified, STATUS_COLORS["good"])
        + "</div>"
    )
    legend_item = lambda color, label, count: (  # noqa: E731
        f'<span><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:{color};margin-right:4px;"></span>{html.escape(label)} ({count})</span>'
    )
    legend = (
        f'<div style="display:flex;gap:16px;margin-top:6px;font-size:12px;color:{TEXT_MUTED};flex-wrap:wrap;">'
        + legend_item(STATUS_COLORS["critical"], "Stated only", stated)
        + legend_item(STATUS_COLORS["warning"], "Explained", explained)
        + legend_item(STATUS_COLORS["good"], "Justified", justified)
        + "</div>"
    )
    gap_html = f'<div style="font-size:12px;color:{TEXT_MUTED};margin-top:6px;">{html.escape(gap)}</div>' if gap else ""
    return f'<div style="margin-bottom:8px;">{bar}{legend}{gap_html}</div>'


def _major_issue_html(n: int, title: str, evidence: str, next_time: str) -> str:
    evidence_html = f'<div style="font-size:13px;color:{TEXT_SECONDARY};margin-bottom:4px;"><strong>Evidence:</strong> {html.escape(evidence)}</div>' if evidence else ""
    next_html = f'<div style="font-size:13px;color:{TEXT_PRIMARY};"><strong>Next time:</strong> {html.escape(next_time)}</div>' if next_time else ""
    return (
        f'<div style="background:{CARD_BG};border:{CARD_BORDER};border-radius:12px;padding:16px 18px;">'
        '<div style="display:flex;gap:10px;align-items:baseline;margin-bottom:8px;">'
        f'<span style="font-family:{FONT_SERIF};font-size:15px;font-weight:700;color:{RATING_ACCENT["warning"]};">{n:02d}</span>'
        f'<span style="font-family:{FONT_SANS};font-size:14.5px;font-weight:600;color:{TEXT_PRIMARY};">{html.escape(title)}</span>'
        f"</div>{evidence_html}{next_html}</div>"
    )


def _signal_stat_html(label: str, value_text: str) -> str:
    return (
        '<div style="flex:1;min-width:140px;">'
        f'<div style="font-size:22px;font-weight:700;color:{TEXT_PRIMARY};">{html.escape(value_text)}</div>'
        f'<div style="font-size:12px;color:{TEXT_MUTED};">{html.escape(label)}</div>'
        "</div>"
    )
