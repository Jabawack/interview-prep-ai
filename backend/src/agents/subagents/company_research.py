"""CompanyResearchAgent — researches interview processes, questions, company culture."""

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.agents.prompts.system import build_company_research_prompt
from src.agents.tools.company_research_tools import (
    get_company_profile,
    get_interview_patterns,
    search_company_questions,
)
from src.config import settings

_model = ChatOpenAI(
    model=settings.agent_model,
    api_key=settings.openai_api_key,
    temperature=0,
)
_checkpointer = MemorySaver()

COMPANY_RESEARCH_TOOLS = [search_company_questions, get_interview_patterns, get_company_profile]

company_research_agent = create_react_agent(
    model=_model,
    tools=COMPANY_RESEARCH_TOOLS,
    prompt=build_company_research_prompt(),
    checkpointer=_checkpointer,
)
