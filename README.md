# Interview Insight

Tools that turn a recorded product-manager interview into structured, actionable coaching feedback.

## 🎯 [ai_pm_interview_coach_agent/](ai_pm_interview_coach_agent/)

A standalone **Streamlit + Claude (Anthropic API)** app — clone it, add your API key, and run it. \
Paste or upload any interview transcript and get a bullet-point report: framework adherence \
(CIRCLES / STAR / Goal→Metric→Diagnose→Recommend), concrete mistakes, sentiment red flags, filler-word \
counts, and a fix per answer. No dependency on any specific meeting tool. See its \
[README](ai_pm_interview_coach_agent/README.md) for setup.

## 🤖 [.claude/agents/pm-interview-coach.md](.claude/agents/pm-interview-coach.md)

The same coaching logic as a **Claude Code subagent**, for anyone who already uses Claude Code with \
Granola connected — invoke it by naming a Granola meeting and it fetches the transcript, analyzes \
it, and saves a report directly, no copy-pasting transcripts required. Requires Claude Code with a \
Granola MCP connector.

Both share the same evaluation approach; pick whichever fits your setup.

## License

MIT — see [LICENSE](LICENSE).
