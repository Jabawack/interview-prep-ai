"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.chat import router as chat_router
from src.api.v1.companies import router as companies_router
from src.api.v1.conversations import router as conversations_router
from src.api.v1.jobs import router as jobs_router
from src.config import API_V1_PREFIX, settings
from src.database import close_pool, get_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: eagerly create DB pool
    await get_pool()
    yield
    # Shutdown: close pool
    await close_pool()


app = FastAPI(title="InterviewPrepAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [chat_router, jobs_router, companies_router, conversations_router]:
    app.include_router(router, prefix=API_V1_PREFIX)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
