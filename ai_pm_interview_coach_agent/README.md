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
**Speaking delivery**. Dimensions without evidence show "Not assessed" instead of a guessed \
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
- 🔗 **Connect Granola, right where you assess** — one merged Assessment tab, not a separate
  "Connect Granola" tab to hunt for. Manual entry is a popover in the top-right corner, always
  one click away; Granola connects below it, landing on the same browse-and-select experience
  either way: pick a call, its summary/transcript flow straight into the assessment.
  - **Sign in via MCP** (any plan, including free Basic) — the primary connect option, the same
    browser OAuth flow Claude Code/Claude.ai/ChatGPT use for Granola, no pasted key. Your recent
    calls load automatically into a browsable list — select one and it fetches the transcript for
    you. See the note below on the fallback path for when a server's response can't be parsed
    into a call list.
  - **API key** (Business/Enterprise plan) — a secondary option under "Have a Granola API key
    instead?"; paste a key, browse recorded interviews by folder.
- 🎨 **A calmer, editorial read** — serif display headlines, an eyebrow-labelled section pattern,
  and status-colored rating cards on a quiet neutral background, so the report reads like a
  debrief you'd actually want to sit with, not a dashboard.

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

Everything lives on one **Assessment** tab now — connect Granola or add a transcript manually, \
whichever you have, without switching views.

**Add a transcript manually**

Click **➕ Add manually** in the top-right corner (a popover, always available regardless of \
Granola connection state). Paste or upload the **transcript**, optionally open **Additional \
context** for the summary/target role/question context/outcome, then click **Run Assessment**.

**Or connect Granola** — pick whichever you have:

- **Sign in via MCP** (any plan, including free Basic, no key needed) — the primary "Connect a \
source" button. Your browser opens Granola's sign-in/approval page; approve access and return to \
the app (it's waiting on a local callback, no copy-pasting a code or URL). Run `pip install mcp` \
first (not in `requirements.txt` by default — see Notes below). Once connected, your recent calls \
load automatically into a browsable, searchable list — filter by title and click **Select** on \
one. If Granola's response for a given account/server can't be parsed into a recognizable call \
list (see the note below on why this can happen), the app falls back to a raw tool console \
instead — pick a tool, check its real input schema, call it, and pull the result in manually with \
**Use as summary** / **Use as transcript**.
- **API key** (Business/Enterprise plan) — open "Have a Granola API key instead?", paste your key \
(`grn_...` — generate one in the Granola desktop app under Settings → API access) and click \
**Connect**. Browse by folder, search loaded titles, and click **Select** on one.

**Then, either way:** clicking **Select** takes you to a dedicated review screen — "This is the \
transcript" — showing exactly what will be assessed (and the summary, when the call carries one), \
with **← Back to calls** to pick a different one instead. Add optional context if you like, click \
**Run Assessment**, and you land on a dedicated report screen: a debrief header, the \
five-dimension rating rubric, conversation signals measured from the transcript, how the answers \
landed, a question-by-question breakdown, an improved-answer rewrite, a practice plan, and the top \
issues found. Download it as markdown, or click **← Start a new assessment** to go back to the \
call list (your Granola connection stays live — no need to reconnect). Check the **Progress Log** \
tab after a few sessions and click **Summarize recurring issues** to see what keeps costing you \
points.

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
- **Granola's REST API (the API key option) requires a Business or Enterprise plan.** The free \
Basic plan doesn't support it at all. **MCP sign-in works on Basic too** — Granola's MCP server is \
available on every plan, though transcript access there is still paid-plan-only, same as \
elsewhere.
- **The MCP browse-and-select view is a best-effort parse, with a raw console as its safety \
net.** Granola publishes tool *names* for third-party MCP clients (`list_meetings`, `get_meetings`, \
`get_meeting_transcript`, `query_granola_meetings`, `list_meeting_folders`, `get_account_info`) but \
not their exact input/output schemas. The app calls `list_meetings` automatically and tries several \
plausible response shapes and field names to build the call list you see — input *schemas* are \
still discovered for real at connect time (never guessed), but the *output* shape for `list_meetings` \
can't be known ahead of time the same way. If your account's server returns something the parser \
doesn't recognize, the app says so and falls back to the raw tool console (call a tool, read the \
raw result, pull it in yourself) rather than showing something silently wrong.
- **MCP sign-in only works when you run this app locally.** It uses a loopback OAuth redirect \
(`http://127.0.0.1:<port>/callback`) — the same native-app pattern `claude mcp add` uses — which \
requires your browser and the app to be on the same machine. It won't work on a shared/hosted \
deployment.
- The `mcp` package pulls in a fairly heavy dependency tree (starlette, uvicorn, pyjwt, etc.), so \
it's deliberately left out of `requirements.txt` and imported only when you use this connection \
method. Install it with `pip install mcp` first.
- Both Granola API keys and OAuth tokens are held in Streamlit session state only (not written to \
disk) and sent solely to `public-api.granola.ai` / `mcp.granola.ai`.
