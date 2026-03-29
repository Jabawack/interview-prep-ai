"""Live model pricing via Upstash Redis cache + LiteLLM GitHub JSON fallback.

Flow: Redis (24hr TTL) → GitHub fetch → hardcoded FALLBACK_PRICES.
All I/O is async to avoid blocking the uvicorn event loop.
"""

from __future__ import annotations

import json
import logging

import httpx

from src.config import FALLBACK_PRICES, SUPPORTED_MODEL_IDS, settings

logger = logging.getLogger(__name__)

_LITELLM_PRICES_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
)
_REDIS_KEY = "model_prices"
_TTL_SECONDS = 86_400  # 24 hours

# Lazy-initialised Redis client (None when Upstash is not configured).
_redis_client = None
_redis_init_done = False


def _get_redis():  # noqa: ANN202
    """Return the async Upstash Redis client, or None if not configured."""
    global _redis_client, _redis_init_done
    if _redis_init_done:
        return _redis_client
    _redis_init_done = True
    if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        from upstash_redis.asyncio import Redis

        _redis_client = Redis(
            url=settings.upstash_redis_rest_url,
            token=settings.upstash_redis_rest_token,
        )
    return _redis_client


async def _fetch_from_redis(model_ids: list[str]) -> dict[str, dict[str, float]] | None:
    """Try to load cached prices from Upstash Redis."""
    redis = _get_redis()
    if redis is None:
        return None
    try:
        raw = await redis.get(_REDIS_KEY)
        if raw is None:
            return None
        data = json.loads(raw) if isinstance(raw, str) else raw
        return {mid: data[mid] for mid in model_ids if mid in data}
    except Exception:
        logger.warning("Redis read failed", exc_info=True)
        return None


async def _fetch_from_github() -> dict[str, dict[str, float]]:
    """Fetch the full LiteLLM pricing JSON from GitHub and filter to supported models."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_LITELLM_PRICES_URL)
        resp.raise_for_status()
    all_models = resp.json()

    filtered: dict[str, dict[str, float]] = {}
    for model_id in SUPPORTED_MODEL_IDS:
        entry = all_models.get(model_id)
        if entry and "input_cost_per_token" in entry:
            filtered[model_id] = {
                "input_cost_per_token": entry["input_cost_per_token"],
                "output_cost_per_token": entry.get("output_cost_per_token", 0),
            }
    return filtered


async def _store_in_redis(prices: dict[str, dict[str, float]]) -> None:
    """Cache prices in Upstash Redis with 24hr TTL."""
    redis = _get_redis()
    if redis is None:
        return
    try:
        await redis.set(_REDIS_KEY, json.dumps(prices), ex=_TTL_SECONDS)
    except Exception:
        logger.warning("Redis write failed", exc_info=True)


async def get_model_prices(
    model_ids: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Return pricing for the requested models.

    Resolution order: Redis cache → GitHub fetch → FALLBACK_PRICES.
    """
    ids = model_ids or SUPPORTED_MODEL_IDS

    # 1. Try Redis
    cached = await _fetch_from_redis(ids)
    if cached and len(cached) == len(ids):
        return cached

    # 2. Cache miss — fetch from GitHub
    try:
        live = await _fetch_from_github()
        if live:
            await _store_in_redis(live)
            result = {mid: live[mid] for mid in ids if mid in live}
            if result:
                return result
    except Exception:
        logger.warning("GitHub price fetch failed, using fallback", exc_info=True)

    # 3. Last resort — hardcoded fallback
    return {mid: FALLBACK_PRICES[mid] for mid in ids if mid in FALLBACK_PRICES}
