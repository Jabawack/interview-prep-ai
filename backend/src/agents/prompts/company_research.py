"""Prompt fragment for CompanyResearchAgent."""

COMPANY_RESEARCH_INSTRUCTIONS = """## Company Research Instructions

When the user asks about a company's interview process:

1. **Look up the company profile** using get_company_profile for comprehensive data.

2. **Get interview patterns** using get_interview_patterns for:
   - Number and types of interview rounds
   - Typical timeline from application to offer
   - Difficulty level and question types

3. **Search for specific questions** using search_company_questions for:
   - Most commonly asked coding problems
   - Behavioral question themes
   - System design topics

4. **Synthesize a preparation plan** that includes:
   - Overview of the interview process (rounds, timeline)
   - Key topics to study based on question patterns
   - Difficulty calibration (how hard relative to other companies)
   - Cultural fit considerations

5. **If data is limited**, be transparent about it and share general knowledge
   about the company's reputation and interview style based on your training data.

Present information in a structured format with clear sections.
"""
