"""3-layer pipeline: Intent Parser → Supervisor (Parallel Agents) → Response Composer.

Orchestration:
  Layer 1 — Deterministic intent parsing (no LLM).
  Layer 2 — Dispatch to specialist agents. When 2+ agents are needed, run in parallel.
  Layer 3 — Deterministic response composition.

Yields SSE-ready event dicts throughout.
Mirrors CommodityAI's pipeline.py with interview-domain agents.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, ToolMessage

from src.agents.graph import AGENT_LABELS, AVAILABLE_AGENTS, create_agent
from src.config import SUPPORTED_MODEL_IDS, settings
from src.services import intent_parser, response_composer
from src.services.usage_tracker import UsageTracker

TOOL_DESCRIPTIONS: dict[str, str] = {
    "search_jobs": "Searching job boards...",
    "get_job_details": "Fetching job posting...",
    "save_job_posting": "Saving job posting...",
    "search_company_questions": "Looking up interview questions...",
    "get_interview_patterns": "Researching interview patterns...",
    "get_company_profile": "Loading company profile...",
    "save_message": "Saving message...",
}


def _step_description(tool_calls: list[dict]) -> str:
    if not tool_calls:
        return "Processing..."
    first = tool_calls[0]["name"]
    return TOOL_DESCRIPTIONS.get(first, f"Running {first}...")


def _build_agent_message(parsed: intent_parser.ParsedIntent, agent_key: str) -> str:
    """Build the user message for a specialist agent, including parsed context."""
    context_parts = [f"User message: {parsed.raw_message}"]

    if parsed.entities:
        context_parts.append("---")
        context_parts.append("Context from intent parser:")
        context_parts.append(f"  - Intent: {parsed.intent}")
        for key, value in parsed.entities.items():
            context_parts.append(f"  - {key}: {value}")

    if agent_key == "job_search":
        context_parts.append("")
        context_parts.append(
            "Your task: Search for relevant jobs based on the user's criteria, "
            "analyze the results, and output your structured JSON response."
        )
    elif agent_key == "company_research":
        context_parts.append("")
        context_parts.append(
            "Your task: Research the company's interview process, common questions, "
            "and culture. Output your structured JSON response."
        )

    return "\n".join(context_parts)


# ---------------------------------------------------------------------------
# Standalone streaming generator
# ---------------------------------------------------------------------------

_SENTINEL_EVENT = "_agent_done"


async def _stream_agent_events(
    agent_key: str,
    model_name: str,
    message: str,
    thread_id: str,
    recursion_limit: int,
    tracker: UsageTracker,
    task_id: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Stream SSE events from one agent run.

    Yields regular SSE events plus a final sentinel with the agent's last text.
    Extracts token_usage from every AIMessage for cost tracking.
    """
    agent = create_agent(agent_key, model_name)
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }

    step_count = 0
    final_text: str | None = None

    def _inject_task_id(data: dict) -> dict:
        if task_id is not None:
            return {**data, "task_id": task_id}
        return data

    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            messages = update.get("messages", [])

            if node_name in ("agent", "model"):
                msg = messages[-1] if messages else None
                if not isinstance(msg, AIMessage):
                    continue

                # --- Token extraction (every AIMessage, not just the final) ---
                if usage := msg.response_metadata.get("token_usage"):
                    tracker.record(usage)

                step_count += 1

                if msg.content and msg.tool_calls:
                    yield {
                        "event": "thought",
                        "data": _inject_task_id({"content": msg.content}),
                    }
                if msg.tool_calls:
                    yield {
                        "event": "step",
                        "data": _inject_task_id(
                            {
                                "current": step_count,
                                "description": _step_description(msg.tool_calls),
                            }
                        ),
                    }
                    for tc in msg.tool_calls:
                        yield {
                            "event": "action",
                            "data": _inject_task_id({"tool": tc["name"], "input": tc["args"]}),
                        }
                elif msg.content:
                    final_text = msg.content

            elif node_name == "tools":
                for tool_msg in messages:
                    if isinstance(tool_msg, ToolMessage):
                        yield {
                            "event": "observation",
                            "data": _inject_task_id(
                                {
                                    "tool": tool_msg.name,
                                    "output": tool_msg.content,
                                    "status": getattr(tool_msg, "status", "ok"),
                                }
                            ),
                        }

    # Sentinel: consumed by caller, NOT forwarded to SSE
    yield {"event": _SENTINEL_EVENT, "data": {"final_text": final_text or ""}}


# ---------------------------------------------------------------------------
# Parallel specialist runner
# ---------------------------------------------------------------------------


async def _run_parallel_specialists(
    tasks: list[tuple[str, str, str, str]],
    model_name: str,
    recursion_limit: int,
    tracker: UsageTracker,
    agent_results: dict[str, str],
) -> AsyncGenerator[dict, None]:
    """Run multiple specialist agents in parallel, yielding interleaved SSE events.

    Each entry in `tasks`: (task_id, agent_key, message, thread_id).
    `agent_results` is mutated: task_id -> final_text.
    """
    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    pending: set[asyncio.Task] = set()

    async def _worker(task_id: str, agent_key: str, message: str, thread_id: str) -> None:
        try:
            async for event in _stream_agent_events(
                agent_key,
                model_name,
                message,
                thread_id,
                recursion_limit,
                tracker,
                task_id=task_id,
            ):
                if event["event"] == _SENTINEL_EVENT:
                    agent_results[task_id] = event["data"]["final_text"]
                else:
                    await queue.put(event)
        except Exception as exc:
            await queue.put(
                {
                    "event": "error",
                    "data": {"message": f"Agent {agent_key} failed: {exc}", "task_id": task_id},
                }
            )
        finally:
            await queue.put({"event": "_worker_done", "data": {"task_id": task_id}})

    try:
        for task_id, agent_key, message, thread_id in tasks:
            t = asyncio.create_task(_worker(task_id, agent_key, message, thread_id))
            pending.add(t)
            t.add_done_callback(pending.discard)

        workers_remaining = len(tasks)
        while workers_remaining > 0:
            event = await queue.get()
            if event is None:
                break
            if event["event"] == "_worker_done":
                workers_remaining -= 1
                continue
            yield event
    finally:
        for t in pending:
            t.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


async def process_message(
    message: str,
    model_name: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Process a user chat message through the 3-layer pipeline.

    Yields dicts with 'event' and 'data' keys for SSE streaming.
    """
    # Resolve model — validate against supported list, fall back to default
    model = model_name if model_name in SUPPORTED_MODEL_IDS else settings.agent_model
    tracker = UsageTracker(model)

    # Layer 1: Deterministic intent parse
    parsed = intent_parser.parse(message)
    yield {
        "event": "parse",
        "data": {
            "intent": parsed.intent,
            "entities": parsed.entities,
            "agents_needed": parsed.agents_needed,
        },
    }

    # Layer 2: Dispatch to specialist agents
    base_thread = uuid.uuid4().hex[:8]
    recursion_limit = settings.agent_max_cycles * 2

    if not parsed.agents_needed:
        # No agents matched — provide a general response
        yield {
            "event": "response",
            "data": {
                "content": "I can help you with job searches, company research, "
                "interview preparation, and salary information. "
                "What would you like to know?",
                "output": {},
            },
        }
        yield {"event": "usage", "data": await tracker.summary()}
        yield {"event": "done", "data": {}}
        return

    # Build specialist tasks
    specialist_tasks: list[tuple[str, str, str, str]] = []
    for i, agent_key in enumerate(parsed.agents_needed):
        if agent_key not in AVAILABLE_AGENTS:
            continue  # Skip agents not yet implemented
        task_id = f"{agent_key}-{i}"
        label = AGENT_LABELS.get(agent_key, agent_key.replace("_", " ").title())
        specialist_tasks.append(
            (
                task_id,
                agent_key,
                _build_agent_message(parsed, agent_key),
                f"{agent_key}-{base_thread}",
            )
        )
        yield {
            "event": "agent_start",
            "data": {"agent": agent_key, "label": label, "task_id": task_id},
        }

    if not specialist_tasks:
        yield {
            "event": "response",
            "data": {
                "content": "The agents needed for this task aren't available yet. "
                "Currently I can search for jobs and research companies.",
                "output": {},
            },
        }
        yield {"event": "usage", "data": await tracker.summary()}
        yield {"event": "done", "data": {}}
        return

    # Run agents
    agent_results: dict[str, str] = {}

    if len(specialist_tasks) == 1:
        # Single agent — run sequentially
        task_id, agent_key, msg, thread_id = specialist_tasks[0]
        async for event in _stream_agent_events(
            agent_key,
            model,
            msg,
            thread_id,
            recursion_limit,
            tracker,
            task_id=task_id,
        ):
            if event["event"] == _SENTINEL_EVENT:
                agent_results[task_id] = event["data"]["final_text"]
            else:
                yield event

    elif len(specialist_tasks) >= 2:
        # Multiple agents — run in parallel
        async for event in _run_parallel_specialists(
            specialist_tasks,
            model,
            recursion_limit,
            tracker,
            agent_results,
        ):
            yield event

    # Layer 3: Deterministic response composition
    if agent_results:
        outputs = [response_composer.parse_agent_output(text) for text in agent_results.values()]
        output = response_composer.merge_outputs(outputs)
    else:
        output = response_composer.AgentOutput(error="No agent produced results.")

    final_content = response_composer.compose(output)
    yield {
        "event": "response",
        "data": {
            "content": final_content,
            "output": {
                "intent": output.intent,
                "entities": output.entities,
                "results": output.results,
                "summary": output.summary,
                "follow_up_suggestions": output.follow_up_suggestions,
                "error": output.error,
            },
        },
    }
    yield {"event": "usage", "data": await tracker.summary()}
    yield {"event": "done", "data": {}}
