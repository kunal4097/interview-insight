# 🎯 AI PM Interview Coach

An AI-powered coaching app that turns a product-manager interview transcript into a structured, \
bullet-point feedback report — built with **Streamlit** and **Claude (Anthropic)**. Paste in a \
transcript from a mock or real interview (Granola, Zoom, Otter, or any plain-text export) and get \
back, per question: which answer framework applies, where you deviated from it, concrete mistakes, \
sentiment red flags, filler-word counts, and exactly what to say differently next time. A running \
log tracks which mistakes keep recurring across sessions, so prep actually compounds.

## 🚀 Features

- 🧭 **Framework-aware grading** — classifies each question (product sense, resume/behavioral, \
analytics/metrics) and grades the answer against the framework interviewers actually expect:
  - **Product sense → CIRCLES** (Comprehend, Identify, Report, Cut, List, Evaluate, Summarize)
  - **Resume/behavioral → STAR** (Situation, Task, Action, Result)
  - **Analytics/metrics → Goal → Metric → Diagnose → Recommend**
- 🚩 **Mistake & sentiment detection** — flags concrete errors and negative-sentiment moments \
(hedging, contradiction, trailing off) with the exact spot in the answer, not vague feedback.
- 🗣️ **Filler-word tracking** — counts "um", "like", "you know", "basically", and other filler \
per answer.
- 🛠️ **Concrete fixes** — a specific rewrite tip per answer, tied to the exact framework step \
that was missed.
- 📈 **Progress log across sessions** — every analysis is appended to a local `progress_log.md`; \
a one-click summary surfaces issues that show up in 2+ sessions, so you know what to actually fix \
before the next round.
- 📥 **Exportable reports** — download any report or the full log as markdown.

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Model:** Claude (Anthropic API) — Sonnet 5, Opus 5, or Haiku 4.5, selectable in the sidebar
- **Storage:** local markdown log file (`progress_log.md`) — no database, no external services

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone <this-repo-url>
   cd ai_pm_interview_coach_agent
   ```

2. **Install dependencies:**
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

1. **Get a transcript** — export or copy the text of a PM interview (mock or real). Granola, \
Zoom, Otter, and most call-recording tools can export a plain-text or `.txt` transcript.
2. **Paste or upload it** in the "Analyze Interview" tab.
3. Click **Analyze Interview** — Claude segments the transcript into Q&A pairs, classifies each \
question, and grades the answer.
4. **Read the report** — an executive summary up top, then a per-question breakdown with \
framework adherence, mistakes, sentiment flags, filler words, and a fix. Download it as markdown.
5. Check the **Progress Log** tab after a few sessions and click **Summarize recurring issues** \
to see what keeps costing you points.

## 📝 Example Input

The app works on any transcript with enough turn-taking to tell questions from answers, e.g.:

```
Interviewer: Let's start with a product sense question. How would you improve Spotify for teenagers?
Candidate: Um, so I guess I'd first look at, like, what teenagers actually want from music...
```

No speaker labels? The app will still do its best to separate questions from answers, but \
labeled transcripts (`Interviewer: / Candidate:`) give more accurate results.

## ⚠️ Notes

- This tool evaluates the **candidate's answers**, not the interviewer's technique.
- Transcripts are sent to the Anthropic API for analysis and are not stored anywhere except your \
local `progress_log.md` — nothing leaves your machine besides the API call itself.
