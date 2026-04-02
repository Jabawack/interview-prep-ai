"""Clerk JWT verification and user sync for FastAPI."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request

from src.config import settings
from src.database import get_pool

logger = logging.getLogger(__name__)


def _extract_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return None


def _decode_clerk_jwt(token: str) -> dict:
    """Decode and verify a Clerk-issued JWT using the PEM public key."""
    if not settings.clerk_jwt_key:
        raise HTTPException(status_code=500, detail="Clerk JWT key not configured")
    try:
        payload = jwt.decode(
            token,
            settings.clerk_jwt_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Validate authorized parties (azp claim)
    azp = payload.get("azp")
    if azp and settings.clerk_authorized_parties:
        if azp not in settings.clerk_authorized_parties:
            raise HTTPException(status_code=401, detail="Unauthorized party")

    return payload


async def _upsert_user(clerk_id: str, email: str | None) -> UUID:
    """Upsert a Clerk user into the Neon users table, return our internal UUID."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users (clerk_id, email)
        VALUES ($1, COALESCE($2, ''))
        ON CONFLICT (clerk_id) DO UPDATE SET email = COALESCE($2, users.email)
        RETURNING id
        """,
        clerk_id,
        email,
    )
    return row["id"]


async def get_current_user(request: Request) -> UUID:
    """FastAPI dependency — requires valid Clerk JWT, returns internal user UUID."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    payload = _decode_clerk_jwt(token)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")
    email = payload.get("email")
    return await _upsert_user(clerk_id, email)


async def get_optional_user(request: Request) -> UUID | None:
    """FastAPI dependency — returns user UUID if authenticated, None otherwise."""
    token = _extract_token(request)
    if not token:
        return None
    try:
        payload = _decode_clerk_jwt(token)
        clerk_id = payload.get("sub")
        if not clerk_id:
            return None
        email = payload.get("email")
        return await _upsert_user(clerk_id, email)
    except HTTPException:
        return None


CurrentUser = Annotated[UUID, Depends(get_current_user)]
OptionalUser = Annotated[UUID | None, Depends(get_optional_user)]
