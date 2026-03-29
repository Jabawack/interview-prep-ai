"""Central agent registry — labels, available keys, and factory re-export."""

from src.agents.factory import create_agent

AGENT_LABELS: dict[str, str] = {
    "job_search": "Job Search",
    "company_research": "Company Research",
}

AVAILABLE_AGENTS: set[str] = set(AGENT_LABELS)

__all__ = ["AGENT_LABELS", "AVAILABLE_AGENTS", "create_agent"]
