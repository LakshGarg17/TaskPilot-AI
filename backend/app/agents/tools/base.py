from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    ok: bool = True
    data: Any = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    error: Optional[str] = None

class BaseTool(ABC):
    name: str
    description: str
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    input_schema: Type[BaseModel]

    def validate_inputs(self, inputs: Dict[str, Any]) -> BaseModel:
        return self.input_schema.model_validate(inputs)

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        """
        Execute the tool with validated inputs and execution context.
        """
        pass
