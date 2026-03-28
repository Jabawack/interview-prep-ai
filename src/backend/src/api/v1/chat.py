"""SSE streaming endpoint for chat — POST /api/v1/chat/stream."""

from __future__ import annotations

import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from ...models.schemas import ChatRequest
from ...services.pipeline import process_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    """Process a chat message via SSE streaming.

    Sends the message through the 3-layer pipeline and streams events
    back to the client as Server-Sent Events.
    """
    async def event_generator():
        async for event in process_message(body.message):
            if await request.is_disconnected():
                break
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"]),
            }

    return EventSourceResponse(
        event_generator(),
        ping=15,
        send_timeout=30,
        headers={"X-Accel-Buffering": "no"},
    )
