"""Shared compose instructions — final output format for all agents."""

COMPOSE_INSTRUCTIONS = """## Final Response Format

When all actions are complete, output ONLY a raw JSON object. No prose, no explanation,
no markdown fences — just the JSON.

{
  "intent": "job_search | company_research | interview_prep | salary_research | general",
  "entities": {
    "company": "...",
    "role": "...",
    "location": "..."
  },
  "results": {
    ... agent-specific structured data ...
  },
  "summary": "A concise 2-3 sentence summary of findings for the user.",
  "follow_up_suggestions": ["suggestion 1", "suggestion 2"],
  "error": null
}
"""
