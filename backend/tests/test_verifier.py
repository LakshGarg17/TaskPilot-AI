import pytest
from app.agents.verification.verifier import Verifier
from app.services.llm.mock_provider import MockLLMProvider

@pytest.mark.asyncio
async def test_verifier_pass():
    verifier = Verifier(MockLLMProvider())
    goal = "Research top AI hackathons"
    step_records = [
        {"step_key": "step_1", "description": "Search web", "tool_name": "web_search", "status": "COMPLETED", "output_data": {"results": ["item1"]}},
        {"step_key": "step_2", "description": "Summarize", "tool_name": "summarize", "status": "COMPLETED", "output_data": {"summary": "Great summary"}}
    ]
    sources = [
        {"title": "AI Builders", "url": "https://example.com/hackathon", "domain": "example.com"}
    ]
    reqs = ["Valid sources present", "Clear summary"]

    result = await verifier.verify(goal, step_records, sources, reqs)
    assert result.passed is True
    assert len(result.checks) >= 3
    assert all(c.passed for c in result.checks)

@pytest.mark.asyncio
async def test_verifier_fails_empty_outputs():
    verifier = Verifier(MockLLMProvider())
    goal = "Research AI hackathons"
    step_records = [
        {"step_key": "step_1", "description": "Search web", "tool_name": "web_search", "status": "COMPLETED", "output_data": None}
    ]
    sources = [
        {"title": "Example", "url": "https://example.com", "domain": "example.com"}
    ]

    checks = verifier.run_rule_checks(goal, step_records, sources)
    empty_check = next(c for c in checks if c.name == "step_outputs_non_empty")
    assert empty_check.passed is False

@pytest.mark.asyncio
async def test_verifier_fails_missing_web_sources():
    verifier = Verifier(MockLLMProvider())
    goal = "Research AI hackathons"
    step_records = [
        {"step_key": "step_1", "description": "Search web", "tool_name": "web_search", "status": "COMPLETED", "output_data": {"items": []}}
    ]
    sources = []  # Empty sources when web tool was used!

    checks = verifier.run_rule_checks(goal, step_records, sources)
    source_check = next(c for c in checks if c.name == "web_sources_present")
    assert source_check.passed is False

@pytest.mark.asyncio
async def test_verifier_fails_malformed_urls():
    verifier = Verifier(MockLLMProvider())
    goal = "Research AI hackathons"
    step_records = [
        {"step_key": "step_1", "description": "Search web", "tool_name": "web_search", "status": "COMPLETED", "output_data": {"ok": True}}
    ]
    sources = [
        {"title": "Bad Source", "url": "not_a_valid_url", "domain": ""}
    ]

    checks = verifier.run_rule_checks(goal, step_records, sources)
    url_check = next(c for c in checks if c.name == "well_formed_urls")
    assert url_check.passed is False
