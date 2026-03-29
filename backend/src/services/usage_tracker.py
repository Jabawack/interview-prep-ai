"""Per-request token usage aggregator with live cost calculation.

Records token_usage from every AIMessage in the LangGraph streaming loop.
Cost = (prompt_tokens × input_cost) + (completion_tokens × output_cost).
"""

from __future__ import annotations

import logging

from src.services.price_cache import get_model_prices

logger = logging.getLogger(__name__)


class UsageTracker:
    """Accumulates token counts across multiple LLM calls in a single pipeline run."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.llm_calls = 0

    def record(self, token_usage: dict) -> None:
        """Record one LLM call's token_usage dict (from AIMessage.response_metadata)."""
        self.llm_calls += 1
        self.prompt_tokens += token_usage.get("prompt_tokens", 0)
        self.completion_tokens += token_usage.get("completion_tokens", 0)
        self.total_tokens += token_usage.get("total_tokens", 0)

    async def summary(self) -> dict:
        """Return a JSON-serialisable usage report for the SSE payload."""
        prices = await get_model_prices([self.model])
        cost_usd = _compute_cost(
            self.model,
            self.prompt_tokens,
            self.completion_tokens,
            prices,
        )
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "cost_usd": cost_usd,
        }


def _compute_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    prices: dict[str, dict[str, float]],
) -> float:
    """Split pricing math. Returns 0.0 and logs a warning if model has no pricing."""
    model_prices = prices.get(model)
    if not model_prices:
        logger.warning("No pricing data for model %s — reporting cost as $0.00", model)
        return 0.0
    cost = (
        prompt_tokens * model_prices["input_cost_per_token"]
        + completion_tokens * model_prices["output_cost_per_token"]
    )
    return round(cost, 6)
