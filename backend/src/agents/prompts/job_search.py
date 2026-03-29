"""Prompt fragment for JobSearchAgent."""

JOB_SEARCH_INSTRUCTIONS = """## Job Search Instructions

When the user asks you to find jobs:

1. **Extract search criteria** from the user's message:
   - Job title/role (e.g. "React Developer", "Staff Engineer")
   - Location (default to "San Jose, CA" if not specified
     — the user is based in the South Bay / NorCal area)
   - Specific job boards to search (default: indeed, linkedin)
   - How recent (default: last 72 hours)

2. **Search for jobs** using the search_jobs tool with the extracted criteria.

3. **Analyze results** and present the top matches:
   - Highlight jobs that best match the user's stated preferences
   - Note salary ranges when available
   - Flag any notable companies

4. **Offer to save** promising postings using save_job_posting.

5. **If the user provides a specific job URL**, use get_job_details to fetch
   the full posting, then analyze it for:
   - Required skills and qualifications
   - Red flags or unusual requirements
   - Salary range (stated or estimated)
   - Company and team information

Always present results in a clear, scannable format.
"""
