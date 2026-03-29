"""SSE streaming endpoint for chat — POST /api/v1/chat/stream."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from src.models.schemas import ChatRequest
from src.services.pipeline import process_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request) -> EventSourceResponse:
    """Process a chat message via SSE streaming.

    Sends the message through the 3-layer pipeline and streams events
    back to the client as Server-Sent Events.
    """

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            async for event in process_message(body.message):
                if await request.is_disconnected():
                    break
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"]),
                }
        except Exception as e:
            logger.exception("Pipeline error")
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Something went wrong: {e}"}),
            }
            yield {
                "event": "done",
                "data": json.dumps({}),
            }

    return EventSourceResponse(
        event_generator(),
        ping=15,
        send_timeout=30,
        headers={"X-Accel-Buffering": "no"},
    )
