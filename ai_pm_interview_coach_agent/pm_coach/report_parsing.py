"""
Everything about turning the model's raw report_md text into structured data: building the
user-turn content sent to the model (build_user_content), pulling a named section out of the
markdown by its header markers (_extract_section, _split_question_sections), and parsing +
repairing the leading JSON summary block (_extract_json_summary, _repair_json_quotes,
_strip_json_block). _repair_json_quotes is a deterministic character-by-character fixup for a
real, recurring model mistake around quote-escaping inside JSON string values - see its own
docstring before touching it. _numeric_status maps a 1-5 rating (or None) to a good/warning/
critical/muted status bucket used by the dashboard's rating cards.
"""
import json
import re


def build_user_content(summary: str, transcript: str, target_role: str, question_context: str, outcome: str) -> str:
    parts = [
        "## Interview Summary",
        summary.strip() if summary.strip() else "Not provided.",
        "\n## Transcript",
        transcript.strip() if transcript.strip() else "Not provided.",
        "\n## Question Context and Target Role",
        (target_role.strip() + (("\n" + question_context.strip()) if question_context.strip() else "")).strip()
        or "Not provided.",
        "\n## Candidate-Reported Outcome",
        outcome if outcome and outcome != "Not provided" else "Not provided.",
    ]
    return "\n".join(parts)


def _extract_section(md: str, start_marker: str, end_marker: str | None) -> str:
    start = md.find(start_marker)
    if start == -1:
        return ""
    end = md.find(end_marker, start + len(start_marker)) if end_marker else -1
    if end == -1:
        # end_marker missing (or none given) - stop at the next top-level header instead of
        # running to end-of-string, so a model output that skips a section never causes this
        # extraction to swallow a later section (e.g. Major Issues) into this one too.
        end = md.find("\n## ", start + len(start_marker))
    return md[start: end if end != -1 else None].strip()
def _numeric_status(value) -> str:
    if value is None:
        return "muted"
    if value >= 4:
        return "good"
    if value == 3:
        return "warning"
    return "critical"


def _repair_json_quotes(s: str) -> str:
    """Best-effort repair for two mirror-image mistakes models make around JSON string
    quoting when a field is meant to carry a verbatim quote (a real, recurring failure -
    see git history): (1) a literal '"' used mid-content instead of being escaped (gets
    escaped here), and (2) a '\\"' written where a bare structural quote was meant - either
    opening a value right after ': '/'['/', ' with no string open yet, or closing one right
    before a structural ','/'}'/']' - both get their spurious backslash dropped. Whether a
    quote is "structural" is decided purely by lookahead (only whitespace then ,}]: follows),
    so a quote embedded in the middle of real content is never touched."""
    out = []
    i, n = 0, len(s)
    in_string = False
    while i < n:
        c = s[i]
        if not in_string:
            if c == '"':
                out.append(c)
                in_string = True
                i += 1
                continue
            if c == "\\" and i + 1 < n and s[i + 1] == '"':
                out.append('"')
                in_string = True
                i += 2
                continue
            out.append(c)
            i += 1
            continue

        # in_string
        if c == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt == '"':
                j = i + 2
                while j < n and s[j] in " \t\r\n":
                    j += 1
                if j >= n or s[j] in ",}]":
                    out.append('"')
                    in_string = False
                else:
                    out.append('\\"')
                i += 2
                continue
            out.append(c)
            out.append(nxt)
            i += 2
            continue
        if c == '"':
            j = i + 1
            while j < n and s[j] in " \t\r\n":
                j += 1
            if j >= n or s[j] in ",}]:":
                out.append(c)
                in_string = False
            else:
                out.append('\\"')
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _extract_json_summary(report_md: str) -> tuple[dict | None, str | None]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", report_md, re.DOTALL)
    if not match:
        return None, "No JSON summary block found in the response."
    raw = match.group(1)
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as e:
        try:
            return json.loads(_repair_json_quotes(raw)), None
        except json.JSONDecodeError:
            return None, f"JSON parse error: {e}"


def _strip_json_block(report_md: str) -> str:
    return re.sub(r"```json\s*\{.*?\}\s*```\n*", "", report_md, count=1, flags=re.DOTALL).strip()


def _split_question_sections(body_md: str) -> dict:
    section4 = _extract_section(body_md, "## 4. Question-by-Question Assessment", "## 5. How The Answers Landed")
    if not section4:
        return {}
    matches = list(re.finditer(r"### Q(\d+)", section4))
    result = {}
    for i, m in enumerate(matches):
        n = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section4)
        result[n] = section4[start:end].strip()
    return result
