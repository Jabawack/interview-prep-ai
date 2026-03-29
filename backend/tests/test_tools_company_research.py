"""Tests for company research tools (mocked — no real DB)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from src.agents.tools.company_research_tools import (
    get_company_profile,
    get_interview_patterns,
    search_company_questions,
)


class TestSearchCompanyQuestions:
    @pytest.mark.asyncio
    async def test_returns_questions_when_found(self, mock_pool, sample_company_row):
        mock_pool.fetchrow = AsyncMock(return_value=sample_company_row)

        result = await search_company_questions.ainvoke({"company_name": "Google"})
        data = json.loads(result)
        assert data["company"] == "Google"
        assert data["source"] == "database"
        assert len(data["questions"]) > 0

    @pytest.mark.asyncio
    async def test_returns_empty_when_not_found(self, mock_pool):
        mock_pool.fetchrow = AsyncMock(return_value=None)

        result = await search_company_questions.ainvoke({"company_name": "UnknownCorp"})
        data = json.loads(result)
        assert data["source"] == "none"
        assert data["questions"] == []


class TestGetInterviewPatterns:
    @pytest.mark.asyncio
    async def test_returns_patterns_when_found(self, mock_pool, sample_company_row):
        mock_pool.fetchrow = AsyncMock(return_value=sample_company_row)

        result = await get_interview_patterns.ainvoke({"company_name": "Google"})
        data = json.loads(result)
        assert data["company"] == "Google"
        assert data["glassdoor_rating"] == 4.4
        assert len(data["interview_rounds"]) == 2

    @pytest.mark.asyncio
    async def test_returns_null_fields_when_not_found(self, mock_pool):
        mock_pool.fetchrow = AsyncMock(return_value=None)

        result = await get_interview_patterns.ainvoke({"company_name": "Unknown"})
        data = json.loads(result)
        assert data["glassdoor_rating"] is None
        assert data["interview_rounds"] == []


class TestGetCompanyProfile:
    @pytest.mark.asyncio
    async def test_returns_full_profile(self, mock_pool, sample_company_row):
        mock_pool.fetchrow = AsyncMock(return_value=sample_company_row)

        result = await get_company_profile.ainvoke({"company_name": "Google"})
        data = json.loads(result)
        assert data["name"] == "Google"
        assert data["industry"] == "Technology"
        assert "Two Sum" in data["common_questions"]

    @pytest.mark.asyncio
    async def test_returns_stub_when_not_found(self, mock_pool):
        mock_pool.fetchrow = AsyncMock(return_value=None)

        result = await get_company_profile.ainvoke({"company_name": "Unknown"})
        data = json.loads(result)
        assert data["name"] == "Unknown"
        assert "message" in data
