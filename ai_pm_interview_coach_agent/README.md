# 🎯 AI PM Interview Coach

An AI-powered PM interview assessment app — built with **Streamlit** and **Claude (Anthropic)**. \
Give it interview notes and/or a transcript from a mock or real product-manager interview and get \
back an anonymous, evidence-backed report: a rating dashboard across reasoning, communication, \
delivery, and interviewer response; a question-by-question breakdown graded against the rubric that \
actually fits each question type; a rewritten "improved answer"; a focused practice plan; and up to \
three evidence-backed issues ranked by how much they hurt the answer. A running log tracks which \
issues keep recurring across sessions, so prep actually compounds.

## 🚀 Features

- 🧭 **Rubric-matched grading** — recognizes 8 PM question types and applies the structure that \
fits each one, without penalizing a candidate for skipping steps that don't apply:
  - Product sense / design, Product improvement, Analytics / metrics, RCA / business \
interpretation, Experimentation, Strategy / prioritization, Behavioral / experience, AI product \
experience
- 📊 **5-dimension rating dashboard** — PM reasoning, Language & communication, Verbal delivery, \
Interviewer response, and Candidate-expressed sentiment, each scored independently (1–5, or \
"Not assessable") with an evidence excerpt and a confidence level (High/Medium/Low) — no decimals, \
no percentiles, no hiring probabilities.
- 🧠 **"Why" assessment** — every major choice is classified as Stated, Explained, or Justified, \
so vague-but-confident answers don't get credit they haven't earned.
- 🎭 **Interviewer response, read honestly** — labeled Positive / Mixed / Concern expressed / \
Neutral / Insufficient evidence, backed by the exact observable basis in the transcript. Never \
infers hiring likelihood from politeness or interview length.
- ✍️ **Improved answer rewrite** — a concise, labeled rewrite of a weak answer showing what \
"good" looks like, without inventing experience or results the candidate didn't have.
- 🎯 **Practice plan** — up to three focused exercises with a measurable success check each.
- 🚨 **Major issues found** — up to three evidence-backed issues, ranked by impact on the answer \
(not by how easy they are to count), each with the evidence, the impact, a better approach, and a \
practice action.
- 🕵️ **Anonymous by design** — names, contact details, employers, and identifying background are \
omitted from every report.
- 📈 **Progress log across sessions** — every assessment appends its Snapshot, Rating Dashboard, \
and Major Issues to a local `progress_log.md`; a one-click summary surfaces what recurs across 2+ \
sessions, so you know what to actually fix before the next round.
- 📥 **Exportable reports** — download any report or the full log as markdown.
- 🔗 **Connect Granola directly** — a "Connect Granola" tab talks to Granola's public API: paste an
API key, browse your recorded interviews by folder, pick one, and its summary/transcript flow
straight into the assessment. No copy-pasting transcripts required. Requires a Granola Business or
Enterprise plan (see Notes below).

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Model:** Claude (Anthropic API) — Sonnet 5, Opus 5, or Haiku 4.5, selectable in the sidebar
- **Granola integration:** Granola's public REST API (`https://public-api.granola.ai/v1`) via `requests`
- **Storage:** local markdown log file (`progress_log.md`) — no database, no external services

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone <this-repo-url>
   cd ai_pm_interview_coach_agent
   ```

2. **Install dependencies** (requires Python 3.10+):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   streamlit run pm_interview_coach.py
   ```

## 🔑 Environment Variables

Provide your **Anthropic API key** in the sidebar when the app opens (get one at \
[console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)). \
Alternatively, set it before launching so the sidebar field pre-fills:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## 🧑‍💻 Usage

**Option A — paste or upload manually (Run Assessment tab)**

1. **Gather what you have** — a summary (e.g. Granola's AI-generated notes), a transcript, or \
both. You need at least one; more context (target role, round type, reported outcome) sharpens the \
assessment but isn't required.
2. Open the **Additional context** expander to add the interview summary, target role, question \
context, and candidate-reported outcome (advanced / offer / rejected / no news yet) — all optional.
3. Paste or upload the **transcript**.
4. Click **Run Assessment**.

**Option B — connect Granola (Connect Granola tab)**

1. Paste your **Granola API key** (`grn_...` — generate one in the Granola desktop app under \
Settings → API access) and click **Connect**. The app makes one live call to verify the key before \
proceeding.
2. **Browse your interviews** — filter by folder, search loaded titles, and click **Select** on \
one. Only meetings with a generated Granola summary appear, per Granola's API.
3. The interview's **summary and transcript load automatically** (the app pages through Granola's \
transcript endpoint itself when a transcript is too large to return inline — no manual work).
4. Add optional context (target role, question context, outcome), then click **Run Assessment on \
this interview**.

**Then, either way:**

5. **Read the report** — Snapshot, then the Rating Dashboard, then a question-by-question \
breakdown, communication notes, an improved-answer rewrite, a practice plan, and the top issues \
found. Download it as markdown.
6. Check the **Progress Log** tab after a few sessions and click **Summarize recurring issues** \
to see what keeps costing you points.

## 📝 Example Input

The app works on any summary or transcript with enough detail to reconstruct the questions asked, \
e.g.:

```
Interviewer: Let's start with a product sense question. How would you improve Spotify for teenagers?
Candidate: Um, so I guess I'd first look at, like, what teenagers actually want from music...
```

No speaker labels or only a summary, no raw transcript? The app still runs, but rates verbal \
delivery and some communication dimensions as "Not assessable" rather than guessing — labeled \
transcripts (`Interviewer: / Candidate:`) and a summary together give the most accurate results.

## ⚠️ Notes

- The interviewer-response dimension is read from the interviewer's *visible reactions* in the \
transcript (follow-ups, affirmations, skepticism) — it is not an evaluation of interviewer \
technique, and it never infers a hiring decision unless the interviewer states one explicitly.
- Every rating requires evidence; where the transcript/summary doesn't support one, the report says \
"Not assessable" instead of guessing.
- The known outcome (if you provide one) is tracked separately and never used to adjust ratings.
- Notes/transcripts are sent to the Anthropic API for analysis and are not stored anywhere except \
your local `progress_log.md` — nothing leaves your machine besides the API calls themselves \
(Anthropic, and Granola if you connect it).
- **Granola API access requires a Business or Enterprise plan.** The free Basic plan doesn't \
support the public API at all (only Granola's MCP server, which is notes-only on Basic) — on \
Basic, use Option A above instead.
- Granola only offers key-based authentication for third-party apps like this one — there's no \
"Sign in with Granola" OAuth flow outside of MCP clients (Claude, ChatGPT, Cursor), so a pasted API \
key is the only way to connect here.
- The Granola API key is held in Streamlit session state only (not written to disk) and is sent \
solely to `public-api.granola.ai`.
