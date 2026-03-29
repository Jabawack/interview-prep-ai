from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    neon_database_url: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]

    # Agent
    agent_max_cycles: int = 10
    agent_model: str = "gpt-4o"

    # Upstash Redis (optional, for price caching)
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # Optional LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "interview-prep-ai"

    model_config = {"env_file": ["../.env.local", ".env.local"], "extra": "ignore"}


settings = Settings()
API_V1_PREFIX = "/api/v1"

# Models users can select from in the UI.
SUPPORTED_MODEL_IDS: list[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
]

# Last-resort fallback when Redis is empty AND GitHub is unreachable (e.g. 429).
# Prices in USD per token. Updated manually — keep in sync with reality.
FALLBACK_PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {"input_cost_per_token": 2.5e-06, "output_cost_per_token": 1e-05},
    "gpt-4o-mini": {"input_cost_per_token": 1.5e-07, "output_cost_per_token": 6e-07},
    "gpt-4.1": {"input_cost_per_token": 2e-06, "output_cost_per_token": 8e-06},
    "gpt-4.1-mini": {"input_cost_per_token": 4e-07, "output_cost_per_token": 1.6e-06},
    "gpt-4.1-nano": {"input_cost_per_token": 1e-07, "output_cost_per_token": 4e-07},
}
