from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# --- Request models ---


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None
    model: str | None = None


class SaveJobRequest(BaseModel):
    title: str
    company: str
    location: str | None = None
    url: str | None = None
    salary_range: str | None = None
    raw_content: str | None = None
    parsed_data: dict = Field(default_factory=dict)


# --- Response models ---


class ConversationOut(BaseModel):
    id: UUID
    title: str
    metadata: dict
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    reasoning_trace: dict | None = None
    created_at: datetime


class JobPostingOut(BaseModel):
    id: UUID
    title: str
    company: str
    location: str | None
    url: str | None
    salary_range: str | None
    parsed_data: dict
    created_at: datetime


class CompanyProfileOut(BaseModel):
    id: UUID
    name: str
    industry: str | None
    interview_rounds: list
    common_questions: list
    glassdoor_rating: float | None
    culture_notes: str | None
    updated_at: datetime


# --- SSE event types ---


class SSEEvent(BaseModel):
    event: str
    data: dict


# --- Intent parser output ---


class ParsedIntent(BaseModel):
    intent: str  # job_search, company_research, interview_prep, general
    entities: dict = Field(default_factory=dict)  # company, role, location, url, etc.
    agents_needed: list[str] = Field(default_factory=list)
    raw_message: str = ""
