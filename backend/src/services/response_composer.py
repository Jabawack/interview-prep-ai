"""Layer 3: Deterministic response composer — merges agent outputs into chat response.

Mirrors CommodityAI's response_composer: extract JSON from agent text, merge parallel
outputs, and compose a human-friendly chat message.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class AgentOutput:
    intent: str = ""
    entities: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    summary: str = ""
    follow_up_suggestions: list[str] = field(default_factory=list)
    error: str | None = None


def _extract_json(text: str) -> dict | None:
    """Robustly extract JSON from agent text — handles markdown fences and prose."""
    if not text:
        return None

    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def parse_agent_output(text: str) -> AgentOutput:
    """Convert agent's final JSON response to AgentOutput."""
    data = _extract_json(text)
    if data is None:
        # Agent returned plain text instead of JSON — wrap it
        return AgentOutput(summary=text[:500], error=None)

    return AgentOutput(
        intent=data.get("intent", ""),
        entities=data.get("entities", {}),
        results=data.get("results", {}),
        summary=data.get("summary", ""),
        follow_up_suggestions=data.get("follow_up_suggestions", []),
        error=data.get("error"),
    )


def merge_outputs(outputs: list[AgentOutput]) -> AgentOutput:
    """Merge multiple AgentOutput objects from parallel agents."""
    if not outputs:
        return AgentOutput(error="No agent outputs to merge.")
    if len(outputs) == 1:
        return outputs[0]

    merged = AgentOutput()
    all_results: dict = {}
    all_suggestions: list[str] = []
    summaries: list[str] = []
    errors: list[str] = []

    for out in outputs:
        if out.error:
            errors.append(out.error)
        if out.intent and not merged.intent:
            merged.intent = out.intent
        if out.entities:
            merged.entities.update(out.entities)
        if out.results:
            all_results.update(out.results)
        if out.summary:
            summaries.append(out.summary)
        all_suggestions.extend(out.follow_up_suggestions)

    merged.results = all_results
    merged.summary = " ".join(summaries)
    # Deduplicate suggestions
    seen: set[str] = set()
    for s in all_suggestions:
        if s not in seen:
            seen.add(s)
            merged.follow_up_suggestions.append(s)

    if errors:
        merged.error = "; ".join(errors)

    return merged


def compose(output: AgentOutput) -> str:
    """Build a human-friendly chat response from AgentOutput."""
    parts: list[str] = []

    if output.error:
        parts.append(f"I ran into an issue: {output.error}")

    if output.summary:
        parts.append(output.summary)

    if output.results:
        # Format results section
        jobs = output.results.get("jobs")
        if jobs and isinstance(jobs, list):
            parts.append(_format_jobs(jobs))

        company = output.results.get("company_profile")
        if company and isinstance(company, dict):
            parts.append(_format_company(company))

    if output.follow_up_suggestions:
        suggestions = "\n".join(f"- {s}" for s in output.follow_up_suggestions[:4])
        parts.append(f"\n**What would you like to do next?**\n{suggestions}")

    if not parts:
        return (
            "I processed your request but didn't find"
            " specific results. Could you provide more details?"
        )
    return "\n\n".join(parts)


def _format_jobs(jobs: list[dict]) -> str:
    """Format job listings for display."""
    lines = [f"**Found {len(jobs)} job(s):**\n"]
    for i, job in enumerate(jobs[:10], 1):
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
        location = job.get("location", "")
        salary = job.get("salary", "")
        url = job.get("url", "")

        site = job.get("site", "")
        site_tag = f"[{site}] " if site else ""
        line = f"{i}. {site_tag}**{title}** at {company}"
        if location:
            line += f" — {location}"
        if salary:
            line += f" ({salary})"
        if url:
            line += f"\n   {url}"
        lines.append(line)

    return "\n".join(lines)


def _format_company(profile: dict) -> str:
    """Format company profile for display."""
    parts = []
    name = profile.get("name", "Unknown")
    parts.append(f"**{name} Interview Overview:**")

    if profile.get("interview_rounds"):
        rounds = profile["interview_rounds"]
        parts.append(f"- **Interview Rounds**: {len(rounds)} stages")
        for r in rounds:
            if isinstance(r, dict):
                parts.append(f"  - {r.get('name', 'Round')}: {r.get('type', '')}")

    if profile.get("glassdoor_rating"):
        parts.append(f"- **Glassdoor Rating**: {profile['glassdoor_rating']}/5.0")

    if profile.get("culture_notes"):
        parts.append(f"- **Culture**: {profile['culture_notes'][:200]}")

    return "\n".join(parts)
