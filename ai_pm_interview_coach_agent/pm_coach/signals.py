"""
Deterministic, computed-not-estimated stats about a transcript: filler word counts, speaking
share, longest answer, question counts. An LLM guessing at these from plain text would produce
fabricated-looking precision, which is exactly what this app's rubric avoids elsewhere - so
these are counted directly with regex/string ops instead of being asked of the model.
"""
import re


# --- Conversation signals (deterministic, computed from the raw transcript text) ------------
# Fillers, speaking share, and longest answer are counted directly, not estimated by the model -
# an LLM guessing at these from plain text would produce fabricated-looking precision, which is
# exactly what this app's rubric is built to avoid elsewhere. Pace/WPM and silence would need real
# timestamps (Granola's transcript items have start_time/end_time; a pasted transcript doesn't) and
# aren't computed here - showing a wrong-but-confident number is worse than omitting it.

FILLER_WORDS = ["um", "uh", "like", "you know", "basically", "actually", "i mean", "sort of", "kind of", "right"]
CANDIDATE_SPEAKER_LABELS = {"candidate", "me", "you"}
INTERVIEWER_SPEAKER_LABELS = {"interviewer", "them", "other speaker"}


def compute_conversation_signals(transcript: str) -> dict:
    if not transcript or not transcript.strip():
        return {}

    lower = transcript.lower()
    filler_total = 0
    filler_breakdown: dict = {}
    for word in FILLER_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        count = len(re.findall(pattern, lower))
        if count:
            filler_breakdown[word] = count
            filler_total += count

    turns: list = []
    for line in transcript.splitlines():
        m = re.match(r"^\s*([A-Za-z][A-Za-z ]{0,30}?):\s*(.*)$", line)
        if m:
            turns.append([m.group(1).strip(), m.group(2).strip()])
        elif turns and line.strip():
            turns[-1][1] += " " + line.strip()

    result: dict = {
        "filler_total": filler_total,
        "filler_breakdown": filler_breakdown,
        "questions_total": transcript.count("?"),
    }

    if not turns:
        result["speakers_identified"] = False
        return result

    labels = {t[0].lower() for t in turns}
    candidate_label = next((l for l in labels if l in CANDIDATE_SPEAKER_LABELS), None)
    interviewer_label = next((l for l in labels if l in INTERVIEWER_SPEAKER_LABELS), None)

    if candidate_label and interviewer_label:
        candidate_words = sum(len(text.split()) for spk, text in turns if spk.lower() == candidate_label)
        interviewer_words = sum(len(text.split()) for spk, text in turns if spk.lower() == interviewer_label)
        total_words = candidate_words + interviewer_words
        if total_words > 0:
            result["speaking_share_pct"] = round(candidate_words / total_words * 100)
        candidate_turns = [text for spk, text in turns if spk.lower() == candidate_label]
        if candidate_turns:
            longest = max(candidate_turns, key=lambda t: len(t.split()))
            result["longest_answer_words"] = len(longest.split())
        result["candidate_questions"] = sum(text.count("?") for spk, text in turns if spk.lower() == candidate_label)
        result["speakers_identified"] = True
    else:
        result["speakers_identified"] = False

    return result
