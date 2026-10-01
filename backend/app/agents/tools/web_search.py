from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.agents.tools.base import BaseTool, ToolResult
from app.services.search import get_search_provider

class WebSearchInput(BaseModel):
    query: str = Field(..., description="The search query to look up on the web")
    max_results: Optional[int] = Field(5, ge=1, le=10, description="Maximum number of search results to return")

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Searches the web for up-to-date information, facts, articles, and documentation."
    risk_level = "LOW"
    input_schema = WebSearchInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        validated = self.validate_inputs(inputs)
        provider = context.get("search_provider") if context else None
        if not provider:
            provider = get_search_provider()

        results = await provider.search(validated.query, max_results=validated.max_results or 5)
        sources = [
            {"title": r.get("title", ""), "url": r.get("url", ""), "domain": r.get("domain", "")}
            for r in results
        ]
        summary = f"Found {len(results)} relevant web results for '{validated.query}'"
        return ToolResult(
            ok=True,
            data=results,
            sources=sources,
            summary=summary
        )
