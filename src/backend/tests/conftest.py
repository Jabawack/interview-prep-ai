"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_pool():
    """Mock asyncpg pool for unit tests — no real DB connection needed.

    Patches get_pool at the module level where tools import it.
    """
    pool = AsyncMock()
    pool.fetchrow = AsyncMock(return_value=None)
    pool.fetch = AsyncMock(return_value=[])
    pool.execute = AsyncMock(return_value="DELETE 0")

    with patch("src.agents.tools.common_tools.get_pool", AsyncMock(return_value=pool)), \
         patch("src.agents.tools.job_search_tools.get_pool", AsyncMock(return_value=pool)), \
         patch("src.agents.tools.company_research_tools.get_pool", AsyncMock(return_value=pool)):
        yield pool


@pytest.fixture
def sample_job_row():
    """Sample job posting row as returned by asyncpg."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Senior React Developer",
        "company": "Google",
        "location": "Remote",
        "url": "https://example.com/job/123",
        "salary_range": "180000-250000",
        "parsed_data": "{}",
        "created_at": "2026-02-23T10:00:00+00:00",
    }


@pytest.fixture
def sample_company_row():
    """Sample company profile row."""
    return {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "Google",
        "industry": "Technology",
        "interview_rounds": '[{"name": "Phone Screen", "type": "behavioral"}, {"name": "Onsite", "type": "coding"}]',
        "common_questions": '["Two Sum", "LRU Cache", "Design Google Search"]',
        "glassdoor_rating": 4.4,
        "culture_notes": "Known for rigorous technical interviews",
        "updated_at": datetime(2026, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
    }
