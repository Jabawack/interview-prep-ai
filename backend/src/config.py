from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    neon_database_url: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]

    # Agent
    agent_max_cycles: int = 10
    agent_model: str = "gpt-4o"

    # Optional LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "interview-prep-ai"

    model_config = {"env_file": ["../.env.local", ".env.local"], "extra": "ignore"}


settings = Settings()
API_V1_PREFIX = "/api/v1"
