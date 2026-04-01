"""Layer 1: Deterministic intent parser — no LLM, pure keyword/regex matching.

Replaces CommodityAI's email_parser. Detects intent, extracts entities (company
names, URLs, roles), and determines which agents to dispatch.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from src.agents.prompts.classify import INTENT_DEFINITIONS
from src.models.schemas import ParsedIntent


def parse(message: str) -> ParsedIntent:
    """Parse a user chat message into a structured intent with entities.

    Returns a ParsedIntent with:
    - intent: best-guess intent category
    - entities: extracted company, role, location, url
    - agents_needed: which specialist agents should run
    """
    lower = message.lower().strip()
    entities: dict = {}

    # Extract URLs
    urls = _extract_urls(message)
    if urls:
        entities["urls"] = urls
        # Classify URL-based intent
        for url in urls:
            domain = urlparse(url).netloc.lower()
            for pattern in INTENT_DEFINITIONS["job_search"].get("url_patterns", []):
                if pattern in domain or pattern in url.lower():
                    entities["job_url"] = url
                    break

    # Extract company names (capitalized words that aren't common words)
    company = _extract_company(message)
    if company:
        entities["company"] = company

    # Extract location hints
    location = _extract_location(lower)
    if location:
        entities["location"] = location

    # Score intents by keyword match
    intent = _classify_intent(lower, entities)

    # Determine which agents are needed
    agents_needed = _route_agents(intent, entities, lower)

    return ParsedIntent(
        intent=intent,
        entities=entities,
        agents_needed=agents_needed,
        raw_message=message,
    )


def _extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    pattern = r"https?://[^\s<>\"')\]]+"
    return re.findall(pattern, text)


def _extract_company(text: str) -> str | None:
    """Extract likely company name from text.

    Looks for patterns like "at Google", "for Meta", "about Amazon".
    """
    patterns = [
        r"(?:at|for|about|from|of|join|joining)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
        r"([A-Z][a-zA-Z]+(?:'s)?)\s+(?:interview|hiring|process|culture|salary|comp)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Filter out common false positives
            if name.lower() not in _COMMON_WORDS:
                return name
    return None


def _extract_location(text: str) -> str | None:
    """Extract location from text."""
    patterns = [
        r"(?:in|near|around)\s+((?:san\s+jose|san\s+francisco|south\s+bay|"
        r"sunnyvale|mountain\s+view|palo\s+alto|santa\s+clara|cupertino|fremont|"
        r"new\s+york|los\s+angeles|seattle|austin|"
        r"boston|chicago|denver|miami|remote|hybrid)[a-z\s,]*)",
        r"(remote|on-?site|hybrid)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
    return None


def _classify_intent(text: str, entities: dict) -> str:
    """Score each intent by keyword matches and return the best one."""
    words = set(re.findall(r"[a-z']+", text))
    scores: dict[str, int] = {}

    for intent_name, intent_def in INTENT_DEFINITIONS.items():
        score = 0
        for keyword in intent_def.get("keywords", []):
            # Multi-word keywords: check substring
            if " " in keyword:
                if keyword in text:
                    score += 2
            else:
                # Single-word: check word presence
                if keyword in words:
                    score += 1

        # Trigger+context pattern for job_search: "find" + "jobs" even if separated
        trigger_words = intent_def.get("trigger_words", [])
        context_words = intent_def.get("context_words", [])
        if trigger_words and context_words:
            has_trigger = any(tw in text for tw in trigger_words)
            has_context = any(cw in words for cw in context_words)
            if has_trigger and has_context:
                score += 3

        # Boost for URL match
        if intent_name == "job_search" and "job_url" in entities:
            score += 3
        scores[intent_name] = score

    # Return highest-scoring intent, or "general" if no matches
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "general"
    return best


def _route_agents(intent: str, entities: dict, raw_lower: str = "") -> list[str]:
    """Determine which agents to dispatch based on intent and entities."""
    agents = []
    has_job_words = bool(re.search(r"\bjobs?\b|\bpositions?\b|\bopenings?\b|\bhiring\b", raw_lower))

    if intent == "job_search":
        agents.append("job_search")
        # Also research the company if one is mentioned
        if entities.get("company"):
            agents.append("company_research")

    elif intent == "company_research":
        agents.append("company_research")
        # Also search jobs if the message mentions jobs
        if has_job_words:
            agents.append("job_search")

    elif intent == "interview_prep":
        # Interview prep might need both company research and general coaching
        if entities.get("company"):
            agents.append("company_research")
        agents.append("job_search")

    elif intent == "salary_research":
        # Phase 2 agent — for now, use company_research as proxy
        if entities.get("company"):
            agents.append("company_research")

    else:
        # General: try to be helpful with whatever we have
        if entities.get("company"):
            agents.append("company_research")
        if has_job_words:
            agents.append("job_search")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for a in agents:
        if a not in seen:
            seen.add(a)
            unique.append(a)

    return unique


_COMMON_WORDS = {
    "the",
    "and",
    "for",
    "are",
    "but",
    "not",
    "you",
    "all",
    "can",
    "had",
    "her",
    "was",
    "one",
    "our",
    "out",
    "day",
    "get",
    "has",
    "him",
    "his",
    "how",
    "its",
    "may",
    "new",
    "now",
    "old",
    "see",
    "way",
    "who",
    "did",
    "let",
    "say",
    "she",
    "too",
    "use",
    "find",
    "tell",
    "what",
    "help",
    "also",
    "been",
    "just",
    "like",
    "look",
    "make",
    "want",
    "will",
    "with",
    "some",
    "that",
    "them",
    "then",
    "they",
    "this",
    "from",
    "have",
    "here",
    "know",
    "more",
    "much",
    "need",
    "over",
    "such",
    "take",
    "than",
    "very",
    "when",
    "come",
    "could",
    "about",
    "would",
    "their",
    "which",
    "other",
    "please",
    "thanks",
    "hello",
    "could",
    "should",
    "interview",
    "remote",
}
