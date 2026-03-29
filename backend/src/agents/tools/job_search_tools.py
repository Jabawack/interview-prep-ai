"""JobSearchAgent tools — search jobs, fetch details, persist postings."""

from __future__ import annotations

import asyncio
import json

import httpx
from jobspy import scrape_jobs
from langchain_core.tools import tool

from src.database import get_pool


@tool
async def search_jobs(
    search_term: str,
    location: str = "San Jose, CA",
    site_names: str = "indeed,linkedin",
    results_wanted: int = 10,
    hours_old: int = 72,
) -> str:
    """Search for job postings across multiple job boards.

    Uses python-jobspy to scrape Indeed, LinkedIn, Glassdoor, and Google Jobs.

    Args:
        search_term: Job title or keywords (e.g. "React Developer", "Staff Engineer").
        location: Location filter (e.g. "Remote", "San Francisco, CA").
        site_names: Comma-separated job boards: indeed,linkedin,google,zip_recruiter.
            Note: glassdoor is blocked by Cloudflare and will not return results.
        results_wanted: Number of results to fetch (default 10, max 50).
        hours_old: Only return postings from the last N hours (default 72).

    Returns:
        JSON array of job postings with title, company, location, url, salary, description.
    """
    sites = [s.strip() for s in site_names.split(",") if s.strip() != "glassdoor"]
    results_wanted = min(results_wanted, 50)

    is_remote = location.lower().strip() in ("remote", "anywhere", "worldwide")

    # jobspy is synchronous — run in a thread
    try:
        df = await asyncio.to_thread(
            scrape_jobs,
            site_name=sites,
            search_term=search_term,
            location=None if is_remote else location,
            is_remote=is_remote,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed="USA",
        )
    except Exception as e:
        return json.dumps({"jobs": [], "error": str(e)})

    if df.empty:
        return json.dumps({"jobs": [], "message": "No jobs found matching criteria."})

    jobs = []
    for _, row in df.iterrows():
        jobs.append(
            {
                "title": str(row.get("title", "")),
                "company": str(row.get("company", "")),
                "location": str(row.get("location", "")),
                "url": str(row.get("job_url", "")),
                "salary": str(row.get("min_amount", "")) + "-" + str(row.get("max_amount", ""))
                if row.get("min_amount")
                else None,
                "description": str(row.get("description", ""))[:500],
                "date_posted": str(row.get("date_posted", "")),
                "site": str(row.get("site", "")),
            }
        )

    return json.dumps({"jobs": jobs, "count": len(jobs)})


@tool
async def get_job_details(job_url: str) -> str:
    """Fetch the full content of a job posting from its URL.

    Args:
        job_url: Direct URL to the job posting.

    Returns:
        JSON with the raw HTML content and extracted text.
    """
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(job_url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

    # Return truncated content to stay within token limits
    content = resp.text[:10_000]
    return json.dumps({"url": job_url, "content": content, "status": resp.status_code})


@tool
async def save_job_posting(
    title: str,
    company: str,
    location: str = "",
    url: str = "",
    salary_range: str = "",
    raw_content: str = "",
    parsed_data: str = "{}",
) -> str:
    """Save a job posting to the database for future reference.

    Args:
        title: Job title.
        company: Company name.
        location: Job location.
        url: URL of the posting.
        salary_range: Salary range string (e.g. "150000-200000").
        raw_content: Raw posting content.
        parsed_data: JSON string of parsed/structured data.

    Returns:
        JSON with the created job posting id.
    """
    pool = await get_pool()
    parsed = json.loads(parsed_data) if isinstance(parsed_data, str) else parsed_data

    row = await pool.fetchrow(
        """
        INSERT INTO job_postings
            (title, company, location, url,
             salary_range, raw_content, parsed_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
        RETURNING id, created_at
        """,
        title,
        company,
        location or None,
        url or None,
        salary_range or None,
        raw_content or None,
        json.dumps(parsed),
    )
    return json.dumps({"id": str(row["id"]), "created_at": row["created_at"].isoformat()})
