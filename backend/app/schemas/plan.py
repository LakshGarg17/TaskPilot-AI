from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    id: str = Field(..., description="Unique step identifier like step_1, step_2")
    description: str = Field(..., description="Clear human-readable description of what this step does")
    tool: str = Field(..., description="Tool name to execute for this step")
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps that must complete before this step")
    input_hints: Dict[str, Any] = Field(default_factory=dict, description="Initial parameters or hints for the tool")
    expected_output: Optional[str] = Field(None, description="What this step is expected to produce")
    risk_level: str = Field("LOW", description="LOW, MEDIUM, or HIGH")

class PlanSchema(BaseModel):
    goal: str = Field(..., description="The overarching user goal being planned")
    steps: List[PlanStep] = Field(..., min_length=1, description="List of discrete steps to execute")
    verification_requirements: List[str] = Field(default_factory=list, description="Verification criteria for success")
