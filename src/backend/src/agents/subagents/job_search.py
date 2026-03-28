"""JobSearchAgent — searches job boards, fetches postings, saves to DB."""

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ...config import settings
from ..middleware import ToolErrorMiddleware
from ..prompts.system import build_job_search_prompt
from ..tools.job_search_tools import get_job_details, save_job_posting, search_jobs

_model = ChatOpenAI(
    model=settings.agent_model,
    api_key=settings.openai_api_key,
    temperature=0,
)
_checkpointer = MemorySaver()

JOB_SEARCH_TOOLS = [search_jobs, get_job_details, save_job_posting]

job_search_agent = create_react_agent(
    model=_model,
    tools=JOB_SEARCH_TOOLS,
    prompt=build_job_search_prompt(),
    checkpointer=_checkpointer,
)
