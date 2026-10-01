from typing import Dict, List, Optional
from app.agents.tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_descriptions(self) -> List[Dict[str, str]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level,
                "schema": t.input_schema.model_json_schema()
            }
            for t in self._tools.values()
        ]

tool_registry = ToolRegistry()
