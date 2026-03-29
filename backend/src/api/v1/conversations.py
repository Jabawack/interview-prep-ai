"""CRUD endpoints for conversations and messages."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.database import get_pool
from src.models.schemas import ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(limit: int = 50, offset: int = 0) -> list[ConversationOut]:
    """List conversations, most recent first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, title, metadata, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit,
        offset,
    )
    return [
        ConversationOut(
            id=r["id"],
            title=r["title"],
            metadata=r["metadata"] if isinstance(r["metadata"], dict) else {},
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(conversation_id: UUID) -> ConversationOut:
    """Get a specific conversation."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, title, metadata, created_at, updated_at FROM conversations WHERE id = $1",
        conversation_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut(
        id=row["id"],
        title=row["title"],
        metadata=row["metadata"] if isinstance(row["metadata"], dict) else {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: UUID, limit: int = 100, offset: int = 0
) -> list[MessageOut]:
    """List messages in a conversation, oldest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, role, content, reasoning_trace, created_at
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
        LIMIT $2 OFFSET $3
        """,
        conversation_id,
        limit,
        offset,
    )
    return [
        MessageOut(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            reasoning_trace=(
                r["reasoning_trace"] if isinstance(r["reasoning_trace"], dict) else None
            ),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: UUID) -> None:
    """Delete a conversation and all its messages."""
    pool = await get_pool()
    result = await pool.execute("DELETE FROM conversations WHERE id = $1", conversation_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Conversation not found")
