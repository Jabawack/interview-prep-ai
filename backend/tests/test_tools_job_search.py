"""Tests for job search tools (mocked — no real scraping or DB)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.tools.job_search_tools import get_job_details, save_job_posting, search_jobs


class TestSearchJobs:
    @pytest.mark.asyncio
    async def test_returns_empty_on_no_results(self):
        """search_jobs returns empty list when jobspy finds nothing."""
        import sys
        import types

        import pandas as pd

        # Mock the jobspy module so `from jobspy import scrape_jobs` works
        mock_jobspy = types.ModuleType("jobspy")
        mock_scrape = MagicMock(return_value=pd.DataFrame())
        mock_jobspy.scrape_jobs = mock_scrape

        with patch.dict(sys.modules, {"jobspy": mock_jobspy}):
            mock_to_thread = AsyncMock(return_value=pd.DataFrame())
            with patch("src.agents.tools.job_search_tools.asyncio") as mock_asyncio:
                mock_asyncio.to_thread = mock_to_thread
                result = await search_jobs.ainvoke(
                    {
                        "search_term": "nonexistent job xyz",
                        "location": "Nowhere",
                    }
                )
        data = json.loads(result)
        assert data["jobs"] == []

    @pytest.mark.asyncio
    async def test_returns_jobs_on_success(self):
        """search_jobs returns formatted jobs from jobspy results."""
        import sys
        import types

        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "title": "React Developer",
                    "company": "Google",
                    "location": "Remote",
                    "job_url": "https://example.com/job/1",
                    "min_amount": 150000,
                    "max_amount": 200000,
                    "description": "Build React apps",
                    "date_posted": "2026-02-20",
                    "site": "indeed",
                }
            ]
        )

        mock_jobspy = types.ModuleType("jobspy")
        mock_jobspy.scrape_jobs = MagicMock(return_value=df)

        with patch.dict(sys.modules, {"jobspy": mock_jobspy}):
            mock_to_thread = AsyncMock(return_value=df)
            with patch("src.agents.tools.job_search_tools.asyncio") as mock_asyncio:
                mock_asyncio.to_thread = mock_to_thread
                result = await search_jobs.ainvoke(
                    {
                        "search_term": "React Developer",
                    }
                )
        data = json.loads(result)
        assert data["count"] == 1
        assert data["jobs"][0]["title"] == "React Developer"
        assert data["jobs"][0]["company"] == "Google"


class TestGetJobDetails:
    @pytest.mark.asyncio
    async def test_fetches_url(self):
        """get_job_details returns content from URL."""
        mock_response = MagicMock()
        mock_response.text = "<html>Job posting content</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("src.agents.tools.job_search_tools.httpx.AsyncClient", return_value=mock_client):
            result = await get_job_details.ainvoke({"job_url": "https://example.com/job/1"})

        data = json.loads(result)
        assert data["url"] == "https://example.com/job/1"
        assert "Job posting content" in data["content"]


class TestSaveJobPosting:
    @pytest.mark.asyncio
    async def test_saves_to_db(self, mock_pool):
        """save_job_posting inserts into job_postings table."""
        mock_pool.fetchrow = AsyncMock(
            return_value={
                "id": "test-uuid",
                "created_at": datetime.now(timezone.utc),
            }
        )

        result = await save_job_posting.ainvoke(
            {
                "title": "React Developer",
                "company": "Google",
                "location": "Remote",
            }
        )
        data = json.loads(result)
        assert data["id"] == "test-uuid"
        mock_pool.fetchrow.assert_called_once()
