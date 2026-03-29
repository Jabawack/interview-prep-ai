"""Tool error middleware — catches tool exceptions and returns them as messages
so the agent can retry with corrected arguments."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import ToolMessage
from pydantic import ValidationError


class ToolErrorMiddleware:
    """Wraps every tool call, converting exceptions to recoverable ToolMessages."""

    async def awrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], Awaitable[ToolMessage]],
    ) -> ToolMessage:
        try:
            return await handler(request)
        except Exception as exc:
            tool_name = request.tool_call["name"]
            error_msg = _format_tool_error(tool_name, exc)
            return ToolMessage(
                content=error_msg,
                name=tool_name,
                tool_call_id=request.tool_call["id"],
                status="error",
            )


def _format_tool_error(tool_name: str, exc: Exception) -> str:
    """Map exceptions to guidance messages the agent can act on."""
    if isinstance(exc, ValidationError):
        fields = [e["loc"][-1] for e in exc.errors()]
        return f"Tool '{tool_name}' validation failed — check fields: {fields}. Fix and retry."

    if isinstance(exc, (KeyError, TypeError)):
        return (
            f"Tool '{tool_name}' received invalid arguments: {exc}. Check argument names and types."
        )

    msg = str(exc)[:200]
    return f"Tool '{tool_name}' error: {msg}. Try a different approach or different arguments."
