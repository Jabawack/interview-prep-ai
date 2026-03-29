"""SSE streaming endpoint for chat — POST /api/v1/chat/stream.
Models listing endpoint — GET /api/v1/chat/models.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from src.config import SUPPORTED_MODEL_IDS, settings
from src.models.schemas import ChatRequest
from src.services.pipeline import process_message
from src.services.price_cache import get_model_prices

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
            async for event in process_message(body.message, model_name=body.model):
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


@router.get("/models")
async def list_models() -> dict:
    """Return supported models with live pricing."""
    prices = await get_model_prices(SUPPORTED_MODEL_IDS)
    models = []
    for model_id in SUPPORTED_MODEL_IDS:
        entry = {"id": model_id}
        if model_id in prices:
            entry["input_cost_per_token"] = prices[model_id]["input_cost_per_token"]
            entry["output_cost_per_token"] = prices[model_id]["output_cost_per_token"]
        models.append(entry)
    return {"models": models, "default": settings.agent_model}
