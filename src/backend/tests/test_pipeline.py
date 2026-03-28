"""Tests for the pipeline orchestration (mocked agents — no LLM calls)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.services.intent_parser import parse
from src.services.response_composer import AgentOutput, compose, merge_outputs, parse_agent_output


class TestResponseComposer:
    def test_extract_json_from_plain(self):
        from src.services.response_composer import _extract_json

        result = _extract_json('{"intent": "job_search"}')
        assert result is not None
        assert result["intent"] == "job_search"

    def test_extract_json_from_markdown_fence(self):
        from src.services.response_composer import _extract_json

        text = 'Here is the result:\n```json\n{"intent": "company_research"}\n```'
        result = _extract_json(text)
        assert result is not None
        assert result["intent"] == "company_research"

    def test_extract_json_from_prose(self):
        from src.services.response_composer import _extract_json

        text = 'Based on my analysis, {"intent": "general", "summary": "hello"} is the output.'
        result = _extract_json(text)
        assert result is not None
        assert result["intent"] == "general"

    def test_parse_agent_output_valid(self):
        text = json.dumps({
            "intent": "job_search",
            "entities": {"company": "Google"},
            "results": {"jobs": [{"title": "SWE"}]},
            "summary": "Found 1 job.",
            "follow_up_suggestions": ["Save this job"],
        })
        output = parse_agent_output(text)
        assert output.intent == "job_search"
        assert output.summary == "Found 1 job."

    def test_parse_agent_output_plain_text(self):
        output = parse_agent_output("I could not find any results.")
        assert output.summary == "I could not find any results."
        assert output.error is None

    def test_merge_outputs_single(self):
        out = AgentOutput(intent="job_search", summary="Found jobs")
        merged = merge_outputs([out])
        assert merged.intent == "job_search"
        assert merged.summary == "Found jobs"

    def test_merge_outputs_multiple(self):
        out1 = AgentOutput(
            intent="job_search",
            summary="Found 5 jobs.",
            results={"jobs": [{"title": "SWE"}]},
            follow_up_suggestions=["Save jobs"],
        )
        out2 = AgentOutput(
            intent="company_research",
            summary="Google has 5 rounds.",
            results={"company_profile": {"name": "Google"}},
            follow_up_suggestions=["Practice questions", "Save jobs"],
        )
        merged = merge_outputs([out1, out2])
        assert "Found 5 jobs" in merged.summary
        assert "Google has 5 rounds" in merged.summary
        assert "jobs" in merged.results
        assert "company_profile" in merged.results
        # Deduplication
        assert merged.follow_up_suggestions.count("Save jobs") == 1

    def test_compose_with_jobs(self):
        output = AgentOutput(
            results={"jobs": [
                {"title": "React Dev", "company": "Google", "location": "Remote"},
            ]},
            summary="Found 1 job matching your criteria.",
        )
        text = compose(output)
        assert "Found 1 job" in text
        assert "React Dev" in text
        assert "Google" in text

    def test_compose_with_error(self):
        output = AgentOutput(error="Something went wrong")
        text = compose(output)
        assert "issue" in text.lower() or "error" in text.lower() or "wrong" in text.lower()

    def test_compose_empty(self):
        output = AgentOutput()
        text = compose(output)
        assert len(text) > 0  # Should still return something helpful


class TestPipelineIntentToAgents:
    """Test that intent parsing correctly determines agent dispatch."""

    def test_parallel_dispatch(self):
        parsed = parse("Find React jobs at Google and tell me about their interview process")
        assert "job_search" in parsed.agents_needed
        assert "company_research" in parsed.agents_needed

    def test_single_dispatch(self):
        parsed = parse("Find React developer jobs")
        assert parsed.agents_needed == ["job_search"]

    def test_no_agents_for_general(self):
        parsed = parse("Hello")
        assert len(parsed.agents_needed) == 0
