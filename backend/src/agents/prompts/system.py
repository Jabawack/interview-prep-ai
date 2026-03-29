"""Prompt assembly — builds complete system prompts per agent from fragments."""

from src.agents.prompts import company_research, compose, job_search

_BASE = """You are an expert AI interview preparation assistant. You help users prepare
for technical interviews by researching companies, finding job postings,
analyzing interview patterns, and providing actionable guidance.

Always be specific and data-driven. When you have data, cite it. When you don't,
say so clearly and offer to help the user find it.
"""


def build_job_search_prompt() -> str:
    return "\n\n".join(
        [
            _BASE,
            "Your specialty is **job search and job posting analysis**.",
            job_search.JOB_SEARCH_INSTRUCTIONS,
            compose.COMPOSE_INSTRUCTIONS,
        ]
    )


def build_company_research_prompt() -> str:
    return "\n\n".join(
        [
            _BASE,
            "Your specialty is **company research and interview pattern analysis**.",
            company_research.COMPANY_RESEARCH_INSTRUCTIONS,
            compose.COMPOSE_INSTRUCTIONS,
        ]
    )
