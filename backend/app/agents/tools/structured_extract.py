from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.agents.tools.base import BaseTool, ToolResult
from app.services.llm import get_llm_provider

class StructuredExtractInput(BaseModel):
    text: str = Field(..., description="The unstructured text or search results to extract entities and fields from")
    fields: Optional[List[str]] = Field(default_factory=list, description="List of target fields to extract per entity")
    schema_description: Optional[str] = Field(None, description="Description of the schema or entity type to extract")

class StructuredExtractTool(BaseTool):
    name = "structured_extract"
    description = "Extracts structured tables, records, or comparison entities from unstructured text into clean JSON."
    risk_level = "LOW"
    input_schema = StructuredExtractInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        validated = self.validate_inputs(inputs)
        llm = context.get("llm_provider") if context else None
        if not llm:
            llm = get_llm_provider()

        fields_desc = ", ".join(validated.fields) if validated.fields else "key comparison metrics, dates, prizes, requirements"
        system_prompt = (
            "You are a precise data extraction specialist. Extract structured records from the text. "
            f"Target fields to extract: {fields_desc}. "
            "Return JSON format: {'items': [{'field1': 'value', ...}], 'headers': ['field1', ...]}"
        )
        prompt = f"Text to extract structured data from:\n{validated.text[:6000]}"

        extracted = await llm.complete_json(prompt=prompt, system_prompt=system_prompt)
        items = extracted.get("items", [])
        return ToolResult(
            ok=True,
            data=extracted,
            summary=f"Extracted {len(items)} structured entities"
        )
