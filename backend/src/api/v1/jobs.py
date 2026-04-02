"""CRUD endpoints for saved job postings."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.api.auth import CurrentUser
from src.database import get_pool
from src.models.schemas import JobPostingOut, SaveJobRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[JobPostingOut])
async def list_jobs(
    user_id: CurrentUser,
    limit: int = 50,
    offset: int = 0,
) -> list[JobPostingOut]:
    """List saved job postings for the authenticated user, most recent first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, title, company, location, url, salary_range, parsed_data, created_at
        FROM job_postings
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id,
        limit,
        offset,
    )
    return [
        JobPostingOut(
            id=r["id"],
            title=r["title"],
            company=r["company"],
            location=r["location"],
            url=r["url"],
            salary_range=r["salary_range"],
            parsed_data=(
                json.loads(r["parsed_data"])
                if isinstance(r["parsed_data"], str)
                else r["parsed_data"]
            ),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{job_id}", response_model=JobPostingOut)
async def get_job(job_id: UUID, user_id: CurrentUser) -> JobPostingOut:
    """Get a specific job posting owned by the authenticated user."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, title, company, location, url,
               salary_range, parsed_data, created_at
        FROM job_postings WHERE id = $1 AND user_id = $2
        """,
        job_id,
        user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return JobPostingOut(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        url=row["url"],
        salary_range=row["salary_range"],
        parsed_data=(
            json.loads(row["parsed_data"])
            if isinstance(row["parsed_data"], str)
            else row["parsed_data"]
        ),
        created_at=row["created_at"],
    )


@router.post("/", response_model=JobPostingOut, status_code=201)
async def create_job(body: SaveJobRequest, user_id: CurrentUser) -> JobPostingOut:
    """Manually save a job posting for the authenticated user."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO job_postings
            (user_id, title, company, location, url,
             salary_range, raw_content, parsed_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        RETURNING id, title, company, location, url,
                  salary_range, parsed_data, created_at
        """,
        user_id,
        body.title,
        body.company,
        body.location,
        body.url,
        body.salary_range,
        body.raw_content,
        json.dumps(body.parsed_data),
    )
    return JobPostingOut(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        url=row["url"],
        salary_range=row["salary_range"],
        parsed_data=(
            json.loads(row["parsed_data"])
            if isinstance(row["parsed_data"], str)
            else row["parsed_data"]
        ),
        created_at=row["created_at"],
    )


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: UUID, user_id: CurrentUser) -> None:
    """Delete a saved job posting owned by the authenticated user."""
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM job_postings WHERE id = $1 AND user_id = $2",
        job_id,
        user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Job posting not found")
