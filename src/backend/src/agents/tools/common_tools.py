"""Shared tools available to all agents."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from ...database import get_pool


@tool
async def save_message(conversation_id: str, role: str, content: str) -> str:
    """Save a message to the conversation history.

    Args:
        conversation_id: UUID of the conversation.
        role: One of 'user', 'assistant', 'system'.
        content: The message text.

    Returns:
        JSON with the created message id.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO messages (conversation_id, role, content)
        VALUES ($1, $2, $3)
        RETURNING id, created_at
        """,
        conversation_id,
        role,
        content,
    )
    return json.dumps({"id": str(row["id"]), "created_at": row["created_at"].isoformat()})
