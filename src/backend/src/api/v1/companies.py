"""CRUD endpoints for company profiles."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...database import get_pool
from ...models.schemas import CompanyProfileOut

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyProfileOut])
async def list_companies(limit: int = 50, offset: int = 0):
    """List company profiles."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, name, industry, interview_rounds, common_questions,
               glassdoor_rating, culture_notes, updated_at
        FROM company_profiles
        ORDER BY name
        LIMIT $1 OFFSET $2
        """,
        limit,
        offset,
    )
    return [_row_to_profile(r) for r in rows]


@router.get("/{company_id}", response_model=CompanyProfileOut)
async def get_company(company_id: UUID):
    """Get a specific company profile."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, name, industry, interview_rounds, common_questions,
               glassdoor_rating, culture_notes, updated_at
        FROM company_profiles WHERE id = $1
        """,
        company_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return _row_to_profile(row)


@router.get("/by-name/{name}", response_model=CompanyProfileOut)
async def get_company_by_name(name: str):
    """Get a company profile by name (case-insensitive)."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, name, industry, interview_rounds, common_questions,
               glassdoor_rating, culture_notes, updated_at
        FROM company_profiles WHERE lower(name) = lower($1)
        """,
        name.strip(),
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Company '{name}' not found")
    return _row_to_profile(row)


def _row_to_profile(row) -> CompanyProfileOut:
    return CompanyProfileOut(
        id=row["id"],
        name=row["name"],
        industry=row["industry"],
        interview_rounds=json.loads(row["interview_rounds"]) if isinstance(row["interview_rounds"], str) else row["interview_rounds"],
        common_questions=json.loads(row["common_questions"]) if isinstance(row["common_questions"], str) else row["common_questions"],
        glassdoor_rating=float(row["glassdoor_rating"]) if row["glassdoor_rating"] else None,
        culture_notes=row["culture_notes"],
        updated_at=row["updated_at"],
    )
