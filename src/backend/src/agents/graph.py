"""Central export for all agents."""

from .subagents.company_research import company_research_agent
from .subagents.job_search import job_search_agent

AGENT_LOOKUP = {
    "job_search": job_search_agent,
    "company_research": company_research_agent,
}

AGENT_LABELS = {
    "job_search": "Job Search",
    "company_research": "Company Research",
}

__all__ = [
    "job_search_agent",
    "company_research_agent",
    "AGENT_LOOKUP",
    "AGENT_LABELS",
]
