# Interview Insight

Tools that turn Granola notes and/or a transcript of a product-manager interview into an anonymous, \
evidence-backed assessment report — a rating dashboard, a question-by-question breakdown against \
the rubric that fits each question type, an improved-answer rewrite, a practice plan, and the top \
evidence-backed issues to fix.

## 🎯 [ai_pm_interview_coach_agent/](ai_pm_interview_coach_agent/)

A standalone **Streamlit + Claude (Anthropic API)** app — clone it, add your API key, and run it. \
Paste or upload a transcript (and/or a summary) and get the full assessment report. No dependency \
on any specific meeting tool. See its [README](ai_pm_interview_coach_agent/README.md) for setup.

## 🤖 [.claude/agents/pm-interview-coach.md](.claude/agents/pm-interview-coach.md)

The same assessment methodology as a **Claude Code subagent**, for anyone who already uses Claude \
Code with Granola connected — invoke it by naming a Granola meeting and it fetches the notes and \
transcript, runs the assessment, and saves a report directly, no copy-pasting required. Requires \
Claude Code with a Granola MCP connector.

Both share the same rubric; pick whichever fits your setup.

## 🔌 Connecting Granola (for the subagent)

The subagent calls **Granola's own official MCP server** — there's nothing custom to host or run. \
Each person who wants to use it connects their own Granola account to Claude:

**Claude web/desktop**
1. Sign in to Claude → Settings → Connectors.
2. Search for "Granola" and click Connect. This opens a browser OAuth flow to authorize Claude to \
read your notes — no API key to copy or paste.
3. Make sure the Granola connector is toggled on for the chat/session you use the subagent in.

**Claude Code (CLI)**
```bash
claude mcp add granola --transport http https://mcp.granola.ai/mcp
```
Start a new `claude` session, run `/mcp`, select `granola`, and choose **Authenticate** (same \
browser OAuth flow, no manual tokens).

**Requirements and caveats**
- Claude web/desktop connectors require a paid Claude subscription.
- A Granola account is required. **Transcript access — the `get_meeting_transcript` tool this \
subagent relies on — needs a Granola Business or Enterprise plan.** The free Basic plan only \
exposes notes/summaries from the last 30 days, not raw transcripts.
- On Granola Basic, the subagent still runs on the summary alone — the rubric supports \
summary-only assessment — but verbal-delivery and some communication-dimension ratings will come \
back "Not assessable" without a transcript.

Don't use Granola, or don't want to connect it? Use the \
[standalone app](ai_pm_interview_coach_agent/) instead — paste or upload any transcript directly, \
no connector required.

## License

MIT — see [LICENSE](LICENSE).
