# 🎯 AI PM Interview Coach

An AI-powered PM interview assessment app — built with **Streamlit** and **Claude (Anthropic)** or \
**OpenAI**. Give it interview notes and/or a transcript from a mock or real product-manager \
interview and get back an anonymous, evidence-backed report built around one hypothesis: \
*candidates improve when they understand how their answers addressed the interviewer's intent, \
where their reasoning became weak or unclear, and what specific behavior to practice next.* Every \
exchange is assessed on its own terms first, and the dashboard is derived from those per-exchange \
assessments — not the other way around.

## 🚀 Features

- 📊 **A dashboard built from per-exchange assessments, not a flat report.** Reading top to \
bottom:
  - **Opening assessment** — the candidate's introduction and first substantive answer, judged on \
relevance to the role, ownership clarity, concrete impact, and concision, kept separate from the \
per-question breakdown.
  - **Answer assessment** — five independent 1-5 coaching ratings, each with evidence: **Answer \
relevance**, **Decision reasoning**, **Metrics and evidence**, **Communication clarity**, and \
**Speaking delivery**. Dimensions without evidence show "Not assessable" instead of a guessed \
score — including Speaking delivery, which is only rated when the transcript is a faithful, \
turn-by-turn capture (and only judges pace/pauses when real timing data exists).
  - **Reasoning depth** — a stacked bar showing how many of the candidate's choices were merely \
*stated*, *explained* with a reason, or fully *justified* against evidence/tradeoffs.
  - **Conversation signals** — filler-word count, candidate speaking share, longest answer, and \
questions asked, computed *deterministically* from the transcript's own text (not estimated by the \
model), with graceful "not available" handling when speakers can't be identified.
  - **How the answers landed** — each notable interviewer reaction classified (explicit positive \
feedback, explicit concern or correction, request for clarification, further exploration, neutral \
acknowledgment, or unclear) with the supporting excerpt, plus any genuine candidate-expressed \
sentiment and what it was about. An outcome signal, never folded into a skill rating.
  - **What worked**, then **major issues** (ranked by impact, each with evidence and a concrete \
next-time action) and a **practice plan** tied to those issues.
  - **Your answers, unpacked** — a per-question expander list, not one long dump.
- 🧭 **Rubric-matched grading** — recognizes 9 PM question types and applies the structure that \
fits each one, without penalizing a candidate for skipping steps that don't apply:
  - Product sense / design, Product improvement, Analytics / metrics, RCA / business \
interpretation, Experimentation, Strategy / prioritization, Technical / systems problem-solving, \
Behavioral / experience, AI product experience
- 🧠 **"Why" assessment** — every major choice is classified as Stated, Explained, or Justified, \
so vague-but-confident answers don't get credit they haven't earned.
- ✍️ **Improved answer rewrite** — a concise, labeled rewrite of a weak answer showing what \
"good" looks like, without inventing experience or results the candidate didn't have.
- 🕵️ **Anonymous by design** — names, contact details, employers, and identifying background are \
omitted from every report.
- 📈 **Progress log across sessions** — every assessment appends its Snapshot, Opening Assessment, \
and Rating Dashboard, plus Major Issues, to a local `progress_log.md`; a one-click summary surfaces \
what recurs across 2+ sessions, so you know what to actually fix before the next round.
- 📥 **Exportable reports** — download any report or the full log as markdown.
- 🔗 **Connect Granola directly** — a "Connect Granola" tab with two connection methods:
  - **API key** (Business/Enterprise plan) — paste a key, browse recorded interviews by folder,
    pick one, and its summary/transcript flow straight into the assessment.
  - **Sign in via MCP** (any plan, including free Basic) — the same browser OAuth flow Claude
    Code/Claude.ai/ChatGPT use for Granola, no pasted key. See the note on this mode below — it's
    a transparent tool console rather than a polished parsed view, since Granola hasn't published
    exact MCP tool schemas for third-party clients.

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Model:** a provider selector in the sidebar switches the whole app between **Claude**
(Anthropic API — Haiku 4.5, Sonnet 5, or Opus 5) and **OpenAI** (GPT-5 Mini, GPT-5.6 Terra, or
GPT-5.6 Sol). Same rubric and report either way — only the API call underneath changes.
- **Granola integration:** Granola's public REST API (`https://public-api.granola.ai/v1`) via
`requests`, plus an optional MCP/OAuth client (`mcp` package, lazy-installed) against
`https://mcp.granola.ai/mcp`
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

## 🔑 API Keys — set once, not every run

Pick a provider in the sidebar, then provide that provider's API key there — Claude \
([console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)) or OpenAI \
([platform.openai.com/api-keys](https://platform.openai.com/api-keys)). You only need the key \
for whichever provider you have selected. To avoid retyping it every time you restart the app \
or open a new browser tab, use either of these (both are read automatically on every run):

**Option A — `.streamlit/secrets.toml` (recommended)**

Edit `ai_pm_interview_coach_agent/.streamlit/secrets.toml` (already created, gitignored — it \
will never be committed) and fill in whichever key(s) you use:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
OPENAI_API_KEY = "sk-..."
```

Restart the app once after saving, and the sidebar field stays pre-filled from then on.

**Option B — environment variable**

```bash
export ANTHROPIC_API_KEY=your_key_here   # for Claude
export OPENAI_API_KEY=your_key_here      # for OpenAI
```

Add this to your shell profile (`~/.zshrc`, etc.) to persist it across terminal sessions. If \
both are set, `.streamlit/secrets.toml` takes precedence.

## 🧑‍💻 Usage

**Option A — paste or upload manually (Run Assessment tab)**

1. **Gather what you have** — a summary (e.g. Granola's AI-generated notes), a transcript, or \
both. You need at least one; more context (target role, round type, reported outcome) sharpens the \
assessment but isn't required.
2. Open the **Additional context** expander to add the interview summary, target role, question \
context, and candidate-reported outcome (advanced / offer / rejected / no news yet) — all optional.
3. Paste or upload the **transcript**.
4. Click **Run Assessment**.

**Option B — connect Granola with an API key (Connect Granola tab)**

1. Paste your **Granola API key** (`grn_...` — generate one in the Granola desktop app under \
Settings → API access) and click **Connect**. The app makes one live call to verify the key before \
proceeding.
2. **Browse your interviews** — filter by folder, search loaded titles, and click **Select** on \
one. Only meetings with a generated Granola summary appear, per Granola's API.
3. The interview's **summary and transcript load automatically** (the app pages through Granola's \
transcript endpoint itself when a transcript is too large to return inline — no manual work).
4. Add optional context (target role, question context, outcome), then click **Run Assessment on \
this interview**.

**Option C — sign in via MCP, no key (Connect Granola tab, "Sign in via MCP")**

1. Run `pip install mcp` (not in `requirements.txt` by default — see Notes below).
2. Switch the connection method to **Sign in via MCP** and click **Sign in with Granola**. Your \
browser opens Granola's sign-in/approval page; approve access and return to the app (it's waiting \
on a local callback, no copy-pasting a code or URL).
3. Once connected, pick a tool (e.g. `list_meetings`), check its real input schema shown above the \
arguments box, fill in `{}` or matching arguments, and click **Call tool**.
4. Click **Use as summary** / **Use as transcript** on the result to pull it into the assessment \
fields below, then **Run Assessment on this content**.

**Then, either way:**

5. **Read the report** — Snapshot and Opening Assessment, then the five-dimension Rating \
Dashboard, a question-by-question breakdown, how the answers landed, an improved-answer rewrite, a \
practice plan, and the top issues found. Download it as markdown.
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
- **Granola's REST API (Option B) requires a Business or Enterprise plan.** The free Basic plan \
doesn't support it at all. **The MCP sign-in (Option C) works on Basic too** — Granola's MCP server \
is available on every plan, though transcript access there is still paid-plan-only, same as \
elsewhere.
- **The MCP mode is intentionally a raw tool console, not a polished parser.** Granola publishes \
tool *names* for third-party MCP clients (`list_meetings`, `get_meetings`, `get_meeting_transcript`, \
`query_granola_meetings`, `list_meeting_folders`, `get_account_info`) but not their exact input/ \
output schemas. Rather than guess parameter names and risk silently-wrong calls, the app discovers \
each tool's real schema at connect time and shows it to you before you call it — call a tool, read \
the raw result, and pull it into the assessment yourself.
- **MCP sign-in only works when you run this app locally.** It uses a loopback OAuth redirect \
(`http://127.0.0.1:<port>/callback`) — the same native-app pattern `claude mcp add` uses — which \
requires your browser and the app to be on the same machine. It won't work on a shared/hosted \
deployment.
- The `mcp` package pulls in a fairly heavy dependency tree (starlette, uvicorn, pyjwt, etc.), so \
it's deliberately left out of `requirements.txt` and imported only when you use this connection \
method. Install it with `pip install mcp` first.
- Both Granola API keys and OAuth tokens are held in Streamlit session state only (not written to \
disk) and sent solely to `public-api.granola.ai` / `mcp.granola.ai`.
