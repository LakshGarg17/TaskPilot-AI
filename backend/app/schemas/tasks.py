import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    goal: str = Field(..., min_length=3, description="Natural language goal for TaskPilot to plan and execute")

class TaskStepResponse(BaseModel):
    id: uuid.UUID
    step_number: int
    step_key: str
    description: str
    tool_name: str
    depends_on: List[str] = []
    input_hints: Dict[str, Any] = {}
    expected_output: Optional[str] = None
    risk_level: str
    status: str
    retry_count: int
    output_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ToolExecutionResponse(BaseModel):
    id: uuid.UUID
    step_id: Optional[uuid.UUID] = None
    tool_name: str
    inputs: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    ok: bool
    sources: List[Dict[str, Any]] = []
    duration_ms: float
    attempt: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TaskResultResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    markdown: str
    tables: List[Dict[str, Any]] = []
    cards: List[Dict[str, Any]] = []
    chart_data: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = []
    email_draft: Optional[Dict[str, Any]] = None
    verification_report: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ApprovalResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    step_id: uuid.UUID
    tool_name: str
    action_summary: str
    inputs: Dict[str, Any]
    risk_level: str
    status: str
    created_at: datetime.datetime
    resolved_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal: str
    status: str
    plan: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None
    steps: List[TaskStepResponse] = []
    tool_executions: List[ToolExecutionResponse] = []
    result: Optional[TaskResultResponse] = None
    approvals: List[ApprovalResponse] = []

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    event_type: str
    step_id: Optional[str] = None
    tool: Optional[str] = None
    message: str
    payload: Dict[str, Any] = {}
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ApprovalDecision(BaseModel):
    approved: bool
