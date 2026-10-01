import pytest
from app.agents.tools.registry import tool_registry
from app.agents.tools.web_search import WebSearchTool
from app.agents.tools.web_extract import WebExtractTool, is_ssrf_safe
from app.agents.tools.calculator import CalculatorTool, safe_calculate
from app.agents.tools.summarize import SummarizeTool
from app.agents.tools.structured_extract import StructuredExtractTool
from app.agents.tools.email_draft import EmailDraftTool
from app.agents.tools.email_send import EmailSendTool
from app.services.search.mock import MockSearchProvider
from app.services.llm.mock_provider import MockLLMProvider

@pytest.mark.asyncio
async def test_tool_registry():
    tools = tool_registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "web_search" in tool_names
    assert "web_extract" in tool_names
    assert "calculator" in tool_names
    assert "summarize" in tool_names
    assert "structured_extract" in tool_names
    assert "email_draft" in tool_names
    assert "email_send" in tool_names

@pytest.mark.asyncio
async def test_web_search_tool():
    tool = WebSearchTool()
    res = await tool.execute({"query": "AI Hackathons 2026", "max_results": 3}, context={"search_provider": MockSearchProvider()})
    assert res.ok is True
    assert len(res.data) > 0
    assert len(res.sources) > 0
    assert "url" in res.sources[0]

@pytest.mark.asyncio
async def test_web_extract_ssrf_protection():
    tool = WebExtractTool()

    # Blocked private and loopback IPs/hosts
    unsafe_urls = [
        "http://127.0.0.1:8080/admin",
        "http://localhost/secret",
        "http://192.168.1.1/router-status",
        "http://10.0.0.5/internal",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "gopher://localhost:70"
    ]
    for url in unsafe_urls:
        assert is_ssrf_safe(url) is False
        res = await tool.execute({"url": url})
        assert res.ok is False
        assert "blocked" in res.error.lower() or "ssrf" in res.error.lower()

@pytest.mark.asyncio
async def test_calculator_tool_valid():
    tool = CalculatorTool()

    # Simple arithmetic
    res1 = await tool.execute({"expression": "100 * (5 + 15) / 2"})
    assert res1.ok is True
    assert res1.data["result"] == 1000

    # Advanced functions and statistics
    res2 = await tool.execute({"expression": "mean([100, 200, 300])"})
    assert res2.ok is True
    assert res2.data["result"] == 200

    res3 = await tool.execute({"expression": "sqrt(144) + min([5, 10, 15])"})
    assert res3.ok is True
    assert res3.data["result"] == 17

@pytest.mark.asyncio
async def test_calculator_tool_rejects_unsafe():
    tool = CalculatorTool()

    unsafe_exprs = [
        "__import__('os').system('whoami')",
        "eval('1+1')",
        "open('file.txt')",
        "exec('x=1')",
        "lambda x: x",
        "import sys",
        "os.popen('dir').read()"
    ]
    for expr in unsafe_exprs:
        res = await tool.execute({"expression": expr})
        assert res.ok is False
        assert "error" in res.error.lower() or "disallowed" in res.error.lower() or "not allowed" in res.error.lower()

@pytest.mark.asyncio
async def test_summarize_tool():
    tool = SummarizeTool()
    res = await tool.execute(
        {"text": "Artificial intelligence hackathons bring together builders worldwide.", "format": "bullet_points"},
        context={"llm_provider": MockLLMProvider()}
    )
    assert res.ok is True
    assert "summary" in res.data
    assert len(res.data["summary"]) > 0

@pytest.mark.asyncio
async def test_structured_extract_tool():
    tool = StructuredExtractTool()
    res = await tool.execute(
        {"text": "Top events: Global AI Hackathon with $100k prize, Frontier Sprint with $50k prize.", "fields": ["name", "prize"]},
        context={"llm_provider": MockLLMProvider()}
    )
    assert res.ok is True
    assert "items" in res.data
    assert len(res.data["items"]) > 0

@pytest.mark.asyncio
async def test_email_draft_tool():
    tool = EmailDraftTool()
    res = await tool.execute(
        {"recipient": "team@example.com", "subject": "Update on AI Hackathons", "context_text": "We found 3 events."},
        context={"llm_provider": MockLLMProvider()}
    )
    assert res.ok is True
    assert res.data["recipient"] == "team@example.com"
    assert "subject" in res.data
    assert "body" in res.data

@pytest.mark.asyncio
async def test_email_send_tool_simulated():
    tool = EmailSendTool()
    res = await tool.execute({
        "to": "partner@example.com",
        "subject": "Collaboration Details",
        "body": "Looking forward to partnering on the AI hackathon submission."
    })
    assert res.ok is True
    assert "simulated" in res.data["status"].lower()
