"""Tests for the intent parser — Layer 1 (no LLM, no DB)."""

from src.services.intent_parser import parse


class TestIntentClassification:
    def test_job_search_basic(self):
        result = parse("Find React developer jobs in Remote")
        assert result.intent == "job_search"
        assert "job_search" in result.agents_needed

    def test_job_search_with_company(self):
        result = parse("Find React jobs at Google")
        assert result.intent == "job_search"
        assert "job_search" in result.agents_needed
        assert "company_research" in result.agents_needed
        assert result.entities.get("company") == "Google"

    def test_company_research(self):
        result = parse("Tell me about Google's interview process")
        assert result.intent == "company_research"
        assert "company_research" in result.agents_needed

    def test_interview_prep(self):
        result = parse("Help me prepare for a technical interview")
        assert result.intent == "interview_prep"

    def test_salary_research(self):
        result = parse("What's the salary for a senior engineer at Meta?")
        assert result.intent == "salary_research"

    def test_general_fallback(self):
        result = parse("Hello, how are you?")
        assert result.intent == "general"

    def test_preserves_raw_message(self):
        msg = "Find Python jobs in San Francisco"
        result = parse(msg)
        assert result.raw_message == msg


class TestEntityExtraction:
    def test_extract_url(self):
        result = parse("Check this job: https://linkedin.com/jobs/view/12345")
        assert "urls" in result.entities
        assert "https://linkedin.com/jobs/view/12345" in result.entities["urls"]

    def test_extract_company_at_pattern(self):
        result = parse("I want to work at Amazon")
        assert result.entities.get("company") == "Amazon"

    def test_extract_company_interview_pattern(self):
        result = parse("What are Meta interview questions?")
        assert result.entities.get("company") == "Meta"

    def test_extract_location_remote(self):
        result = parse("Find jobs in remote")
        assert result.entities.get("location") == "Remote"

    def test_extract_location_city(self):
        result = parse("Find jobs in San Francisco")
        assert result.entities.get("location") is not None
        assert "San Francisco" in result.entities["location"]

    def test_no_false_positive_company(self):
        result = parse("Find remote jobs please")
        assert result.entities.get("company") is None


class TestAgentRouting:
    def test_job_search_routes_single(self):
        result = parse("Find Python developer positions")
        assert result.agents_needed == ["job_search"]

    def test_company_research_routes_single(self):
        result = parse("What's the interview process at Netflix?")
        assert "company_research" in result.agents_needed

    def test_dual_agent_dispatch(self):
        result = parse("Find React jobs at Google and tell me about their interview process")
        assert "job_search" in result.agents_needed
        assert "company_research" in result.agents_needed

    def test_no_duplicate_agents(self):
        result = parse("Find jobs at Google")
        agent_counts = {}
        for a in result.agents_needed:
            agent_counts[a] = agent_counts.get(a, 0) + 1
        for count in agent_counts.values():
            assert count == 1, "Agent should not appear more than once"

    def test_job_url_triggers_job_search(self):
        result = parse("Analyze this posting: https://indeed.com/job/react-dev-123")
        assert "job_search" in result.agents_needed
