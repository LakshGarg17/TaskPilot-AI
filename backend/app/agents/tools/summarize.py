from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.agents.tools.base import BaseTool, ToolResult
from app.services.llm import get_llm_provider

class SummarizeInput(BaseModel):
    text: str = Field(..., description="Text or content to summarize")
    focus: Optional[str] = Field(None, description="Specific topic or angle to emphasize in the summary")
    format: Optional[str] = Field("bullet_points", description="Desired format: bullet_points, executive, or report")

class SummarizeTool(BaseTool):
    name = "summarize"
    description = "Synthesizes and summarizes text, search results, or extracted articles into structured insights."
    risk_level = "LOW"
    input_schema = SummarizeInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        validated = self.validate_inputs(inputs)
        llm = context.get("llm_provider") if context else None
        if not llm:
            llm = get_llm_provider()

        system_prompt = (
            "You are an expert analytical synthesizer. Summarize the provided content accurately, highlighting key metrics, "
            "dates, and findings. Be factual, concise, and structured. Do not invent information."
        )
        prompt = f"Format: {validated.format}\n"
        if validated.focus:
            prompt += f"Focus: {validated.focus}\n"
        prompt += f"\nContent to summarize:\n{validated.text[:6000]}"

        summary_text = await llm.complete_text(prompt=prompt, system_prompt=system_prompt)
        return ToolResult(
            ok=True,
            data={"summary": summary_text},
            summary=f"Synthesized content ({len(summary_text)} chars) into {validated.format} format"
        )
