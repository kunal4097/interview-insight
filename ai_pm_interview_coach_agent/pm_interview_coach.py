"""
AI PM Interview Coach
Turns a product-manager interview transcript into a structured, bullet-point
coaching report: framework adherence (CIRCLES / STAR / Goal-Metric-Diagnose-
Recommend), concrete mistakes, sentiment red flags, filler-word usage, and a
fix per answer. Tracks recurring issues across sessions in a local log.
"""

import os
from datetime import datetime

import streamlit as st
from anthropic import Anthropic

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(APP_DIR, "progress_log.md")

MODELS = {
    "Claude Sonnet 5 (recommended)": "claude-sonnet-5",
    "Claude Opus 5 (deepest analysis)": "claude-opus-5",
    "Claude Haiku 4.5 (fastest/cheapest)": "claude-haiku-4-5-20251001",
}

PM_SKILLS = [
    "Product Sense & Customer Empathy",
    "Prioritization & Trade-off Reasoning",
    "Structured / Analytical Thinking",
    "Communication & Clarity",
    "Execution & Ownership",
    "Leadership & Influence",
]

SYSTEM_PROMPT = """You are a blunt, specific PM interview coach. You are given a transcript of a \
product-manager interview (real or mock) and you turn it into an actionable coaching report for \
the person who answered the questions (the "candidate"). Your primary job is evaluating the \
candidate's answers - but you also read the interviewer's reactions in the transcript as a signal \
of how the interview is landing, since that's information the candidate can't easily judge for \
themselves in the moment.

## Step 1 - Segment into Q&A pairs
Walk the transcript and split it into interviewer-question / candidate-answer pairs. Ignore small \
talk, scheduling chatter, and interviewer monologue that isn't a question. Keep pairs in order. If \
the transcript has no speaker labels, use your best judgment to separate questions from answers.

## Step 2 - Classify each question
Tag each question as one of:
- Product sense - design/build/improve a product, prioritize features, evaluate a product
- Resume / behavioral - "tell me about a time...", walk through a past project, why this role/company
- Analytics / metrics - define success metrics, diagnose a metric drop, A/B test interpretation
- Other - strategy, estimation, execution, or anything that doesn't fit cleanly

## Step 3 - Evaluate each answer against the right framework
- Product sense -> CIRCLES: Comprehend the situation, Identify the customer, Report the customer's \
needs, Cut through prioritization, List solutions, Evaluate trade-offs, Summarize a recommendation.
- Resume / behavioral -> STAR: Situation, Task, Action, Result (bonus: Learning/reflection).
- Analytics / metrics -> Goal -> Metric -> Diagnose -> Recommend: clarify the business goal first, \
define the right metric(s) (one primary + guardrails), structure a diagnosis (segment/compare/\
hypothesize) rather than guessing, end with a concrete recommendation.
- Other -> judge on basic structure: clear point, logical flow, a conclusion.

For every answer capture:
1. Framework adherence - which steps were hit/missed, one line
2. Concrete mistakes - specific, quotable moments, not vague feedback
3. Sentiment/negative signals - hedging ("I guess", "maybe", "I'm not sure"), contradiction, \
defensiveness, trailing off, low-confidence phrasing. Only flag what's actually in the transcript.
4. Filler words - count and list occurrences of: um, uh, like, you know, basically, actually, \
I mean, sort of, kind of, just, right (as a filler)
5. Interviewer reaction - read the interviewer's next turn for engagement cues: deeper follow-up \
questions, affirmations ("great", "that makes sense"), skepticism ("hmm, okay", pushing back, \
challenging the number), abrupt topic changes, or cutting the answer short. Only report this if \
the transcript actually shows the interviewer's next turn - if it's not there, write "No signal in \
transcript" rather than guessing.
6. The fix - 1-2 concrete sentences on exactly what to say or do differently next time, tied to the \
specific missed framework step. Not generic advice.

## Step 4 - Score PM skills across the whole interview
Rate the candidate on each of these six skills, drawing on evidence from across all answers (not \
just one question): Product Sense & Customer Empathy, Prioritization & Trade-off Reasoning, \
Structured / Analytical Thinking, Communication & Clarity, Execution & Ownership, Leadership & \
Influence. For each skill give a rating of Strong / Adequate / Weak / Not enough signal, 1-2 lines \
of evidence quoted or paraphrased from the transcript, and a specific improvement action. Use "Not \
enough signal" honestly when the interview didn't include questions that would surface that skill \
(e.g. no behavioral question asked -> Execution & Ownership and Leadership & Influence likely have \
no signal) - do not force a rating you don't have evidence for.

## Step 5 - Read interviewer sentiment across the interview
Using the per-question interviewer-reaction notes from Step 3, describe the overall trajectory: did \
the interviewer's engagement warm up, cool off, stay flat, or swing based on specific answers? Name \
the 1-2 answers that produced the clearest positive reaction and the 1-2 that produced the clearest \
negative or disengaged reaction, with what specifically triggered each. If the transcript doesn't \
give enough interviewer-side signal to say anything, state that plainly instead of inventing a trend.

## Step 6 - Output format
Clean markdown, headers + bullet points only, no prose paragraphs. Exactly this structure:

# Interview Coaching Report

## Executive Summary
- Overall read: <1 line>
- Top 3 recurring mistakes across the interview
- Total filler-word count (breakdown by word)
- Framework adherence by category
- Interviewer sentiment trend: <1 line>

## Skill Breakdown
### <Skill name>
- Rating: Strong / Adequate / Weak / Not enough signal
- Evidence: ...
- Improvement needed: ...

(repeat for each of the 6 skills)

## Interviewer Sentiment
- Overall trend: ...
- Positive moments: <question ref> - what triggered it
- Negative/disengaged moments: <question ref> - what triggered it

## Q1 - <question text, truncated> [Category: ...]
- Framework adherence: ...
- Mistakes: ...
- Sentiment flags: ...
- Filler words: ...
- Interviewer reaction: ...
- Fix: ...

(repeat per question)

Be direct. No hedging in your own feedback. Bullets only, never paragraphs."""

SUMMARY_SYSTEM_PROMPT = """You are reviewing a log of multiple past PM-interview coaching sessions \
for the same candidate. Identify issues that recur across 2 or more sessions (not one-off mistakes) \
and produce a short bullet list titled "## Recurring Issues" - what keeps happening, and the single \
highest-leverage thing to fix before the next interview. Bullets only."""


def call_claude(client: Anthropic, model: str, system: str, user_content: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def append_to_log(candidate: str, report_md: str) -> None:
    entry_lines = [f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} - {candidate or 'Untitled session'}\n"]
    exec_summary_start = report_md.find("## Executive Summary")
    if exec_summary_start != -1:
        next_heading = report_md.find("\n## ", exec_summary_start + 1)
        exec_summary = report_md[exec_summary_start:next_heading if next_heading != -1 else None]
        entry_lines.append(exec_summary.strip() + "\n")
    else:
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


st.set_page_config(page_title="AI PM Interview Coach", page_icon="🎯", layout="wide")

with st.sidebar:
    st.header("🔑 Settings")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Get one at https://console.anthropic.com/settings/keys",
    )
    model_label = st.selectbox("Model", list(MODELS.keys()))
    model = MODELS[model_label]
    st.divider()
    candidate_name = st.text_input("Candidate / session label", placeholder="e.g. Mock round 2 - product sense")
    st.divider()
    st.caption("Transcripts stay local to this app - the only network call is to the Anthropic API.")

st.title("🎯 AI PM Interview Coach")
st.caption(
    "Paste or upload a product-manager interview transcript (Granola export, Zoom transcript, "
    "or any plain text) and get a bullet-point coaching report: framework adherence, mistakes, "
    "sentiment red flags, filler words, and concrete fixes - per answer, plus a skill breakdown "
    "and a read on how the interviewer was reacting."
)
st.caption("**Skills scored:** " + " · ".join(PM_SKILLS))

tab_analyze, tab_log = st.tabs(["📝 Analyze Interview", "📈 Progress Log"])

with tab_analyze:
    upload = st.file_uploader("Upload a transcript (.txt)", type=["txt"])
    default_text = upload.read().decode("utf-8") if upload else ""
    transcript = st.text_area(
        "Or paste the transcript here",
        value=default_text,
        height=300,
        placeholder="Interviewer: Let's start with a product sense question...\nCandidate: Sure, so I'd first want to understand...",
    )

    analyze_clicked = st.button("Analyze Interview", type="primary", use_container_width=True)

    if analyze_clicked:
        if not api_key:
            st.error("Add your Anthropic API key in the sidebar first.")
        elif not transcript.strip():
            st.error("Paste or upload a transcript first.")
        else:
            with st.spinner("Reviewing the transcript..."):
                client = Anthropic(api_key=api_key)
                report_md = call_claude(client, model, SYSTEM_PROMPT, transcript)
                append_to_log(candidate_name, report_md)
            st.session_state["last_report"] = report_md
            st.success(f"Done. Logged to `{os.path.basename(LOG_PATH)}`.")

    if "last_report" in st.session_state:
        st.divider()
        st.markdown(st.session_state["last_report"])
        st.download_button(
            "Download report (.md)",
            data=st.session_state["last_report"],
            file_name=f"interview-report-{datetime.now().strftime('%Y%m%d-%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

with tab_log:
    log_content = read_log()
    if not log_content.strip():
        st.info("No sessions logged yet - run an analysis first.")
    else:
        st.markdown(log_content)
        if st.button("Summarize recurring issues across all sessions"):
            if not api_key:
                st.error("Add your Anthropic API key in the sidebar first.")
            else:
                with st.spinner("Looking for patterns across sessions..."):
                    client = Anthropic(api_key=api_key)
                    summary = call_claude(client, model, SUMMARY_SYSTEM_PROMPT, log_content)
                st.markdown(summary)
        st.download_button(
            "Download full log (.md)",
            data=log_content,
            file_name="progress_log.md",
            mime="text/markdown",
            use_container_width=True,
        )
