"""Agent factory — creates fresh ReAct agents per request with dynamic model selection.

Replaces the old module-level singletons in subagents/*.py.
Tool lists are stateless and safe to share at module level.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.agents.prompts.system import build_company_research_prompt, build_job_search_prompt
from src.agents.tools.company_research_tools import (
    get_company_profile,
    get_interview_patterns,
    search_company_questions,
)
from src.agents.tools.job_search_tools import get_job_details, save_job_posting, search_jobs
from src.config import settings

JOB_SEARCH_TOOLS = [search_jobs, get_job_details, save_job_posting]
COMPANY_RESEARCH_TOOLS = [search_company_questions, get_interview_patterns, get_company_profile]

_AGENT_CONFIG: dict[str, dict] = {
    "job_search": {
        "tools": JOB_SEARCH_TOOLS,
        "prompt_fn": build_job_search_prompt,
    },
    "company_research": {
        "tools": COMPANY_RESEARCH_TOOLS,
        "prompt_fn": build_company_research_prompt,
    },
}


def create_agent(agent_key: str, model_name: str):  # noqa: ANN201
    """Create a fresh ReAct agent with the given model."""
    cfg = _AGENT_CONFIG[agent_key]
    llm = ChatOpenAI(
        model=model_name,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    return create_react_agent(
        model=llm,
        tools=cfg["tools"],
        prompt=cfg["prompt_fn"](),
        checkpointer=MemorySaver(),
    )
