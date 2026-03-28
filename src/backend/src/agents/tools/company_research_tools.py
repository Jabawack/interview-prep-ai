"""CompanyResearchAgent tools — interview questions, patterns, and company profiles."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from ...database import get_pool


@tool
async def search_company_questions(company_name: str) -> str:
    """Search for interview questions commonly asked at a specific company.

    Queries the local company_profiles table and returns common coding/behavioral
    questions associated with the company.

    Args:
        company_name: Name of the company (e.g. "Google", "Meta", "Amazon").

    Returns:
        JSON with company questions, difficulty distribution, and question categories.
    """
    pool = await get_pool()

    row = await pool.fetchrow(
        """
        SELECT name, common_questions, interview_rounds
        FROM company_profiles
        WHERE lower(name) = lower($1)
        """,
        company_name.strip(),
    )

    if row:
        return json.dumps({
            "company": row["name"],
            "questions": json.loads(row["common_questions"]) if row["common_questions"] else [],
            "rounds": json.loads(row["interview_rounds"]) if row["interview_rounds"] else [],
            "source": "database",
        })

    # No local data — return guidance for the agent to inform the user
    return json.dumps({
        "company": company_name,
        "questions": [],
        "rounds": [],
        "source": "none",
        "message": f"No stored data for {company_name}. Consider researching on Glassdoor or LeetCode.",
    })


@tool
async def get_interview_patterns(company_name: str) -> str:
    """Get the interview process patterns for a company — rounds, timeline,
    difficulty level, and common question types.

    Args:
        company_name: Name of the company.

    Returns:
        JSON with interview rounds, timeline, and difficulty data.
    """
    pool = await get_pool()

    row = await pool.fetchrow(
        """
        SELECT name, interview_rounds, glassdoor_rating, culture_notes, updated_at
        FROM company_profiles
        WHERE lower(name) = lower($1)
        """,
        company_name.strip(),
    )

    if row:
        return json.dumps({
            "company": row["name"],
            "interview_rounds": json.loads(row["interview_rounds"]) if row["interview_rounds"] else [],
            "glassdoor_rating": float(row["glassdoor_rating"]) if row["glassdoor_rating"] else None,
            "culture_notes": row["culture_notes"],
            "last_updated": row["updated_at"].isoformat() if row["updated_at"] else None,
        })

    return json.dumps({
        "company": company_name,
        "interview_rounds": [],
        "glassdoor_rating": None,
        "culture_notes": None,
        "message": f"No interview pattern data for {company_name}.",
    })


@tool
async def get_company_profile(company_name: str) -> str:
    """Get a comprehensive company profile including culture, ratings,
    interview process, and question types.

    Args:
        company_name: Name of the company.

    Returns:
        JSON with the full company profile, or a stub if not found.
    """
    pool = await get_pool()

    row = await pool.fetchrow(
        """
        SELECT id, name, industry, interview_rounds, common_questions,
               glassdoor_rating, culture_notes, updated_at
        FROM company_profiles
        WHERE lower(name) = lower($1)
        """,
        company_name.strip(),
    )

    if row:
        return json.dumps({
            "id": str(row["id"]),
            "name": row["name"],
            "industry": row["industry"],
            "interview_rounds": json.loads(row["interview_rounds"]) if row["interview_rounds"] else [],
            "common_questions": json.loads(row["common_questions"]) if row["common_questions"] else [],
            "glassdoor_rating": float(row["glassdoor_rating"]) if row["glassdoor_rating"] else None,
            "culture_notes": row["culture_notes"],
            "last_updated": row["updated_at"].isoformat() if row["updated_at"] else None,
        })

    return json.dumps({
        "name": company_name,
        "industry": None,
        "interview_rounds": [],
        "common_questions": [],
        "glassdoor_rating": None,
        "culture_notes": None,
        "message": f"No profile found for {company_name}. I'll share general knowledge instead.",
    })
