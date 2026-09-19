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

## License

MIT — see [LICENSE](LICENSE).
