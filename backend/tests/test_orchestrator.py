import asyncio
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import User, Task, TaskStep, ToolExecution, TaskResult, Approval, TaskEvent
from app.agents.orchestrator.orchestrator import orchestrator
from app.agents.tools.registry import tool_registry
from app.agents.tools.base import BaseTool, ToolResult
from tests.conftest import TestingSessionLocal
from pydantic import BaseModel

class DummyFailThenSucceedTool(BaseTool):
    name = "dummy_retry_tool"
    description = "Fails on first attempt, succeeds on second"
    risk_level = "LOW"
    class Schema(BaseModel):
        val: str = "test"
    input_schema = Schema

    def __init__(self):
        self.attempts = 0

    async def execute(self, inputs, context=None):
        self.attempts += 1
        if self.attempts == 1:
            return ToolResult(ok=False, error="Simulated transient glitch")
        return ToolResult(ok=True, data={"status": "recovered"}, summary="Recovered successfully")

class DummyAlwaysFailTool(BaseTool):
    name = "dummy_always_fail_tool"
    description = "Always fails"
    risk_level = "LOW"
    class Schema(BaseModel):
        val: str = "fail"
    input_schema = Schema

    async def execute(self, inputs, context=None):
        return ToolResult(ok=False, error="Permanent failure")

@pytest.fixture(autouse=True)
def register_dummy_tools():
    retry_tool = DummyFailThenSucceedTool()
    fail_tool = DummyAlwaysFailTool()
    tool_registry.register(retry_tool)
    tool_registry.register(fail_tool)
    yield
    tool_registry._tools.pop("dummy_retry_tool", None)
    tool_registry._tools.pop("dummy_always_fail_tool", None)

@pytest.mark.asyncio
async def test_orchestrator_full_execution(db_session):
    user = User(email="orch_user@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = Task(user_id=user.id, goal="Research top AI hackathons and create report", status="PENDING")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task_id = task.id

    # Run task synchronously
    await orchestrator.run_task(task_id)

    # Verify with fresh session
    async with TestingSessionLocal() as session:
        res = await session.execute(
            select(Task)
            .options(
                selectinload(Task.steps),
                selectinload(Task.tool_executions),
                selectinload(Task.result),
                selectinload(Task.events)
            )
            .where(Task.id == task_id)
        )
        completed_task = res.scalar_one()

    assert completed_task.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS")
    assert len(completed_task.steps) >= 2
    assert completed_task.result is not None
    assert "Mission Report" in completed_task.result.markdown
    assert len(completed_task.events) > 5

@pytest.mark.asyncio
async def test_orchestrator_retry_success(db_session):
    user = User(email="retry_user@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = Task(user_id=user.id, goal="Test retry flow", status="RUNNING")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task_id = task.id

    step = TaskStep(
        task_id=task_id,
        step_number=1,
        step_key="step_1",
        description="Run flaky tool",
        tool_name="dummy_retry_tool",
        depends_on=[],
        input_hints={"val": "retry_me"},
        risk_level="LOW",
        status="PENDING"
    )
    task.plan = {"goal": "Test retry flow", "steps": [{"id": "step_1", "description": "Run flaky tool", "tool": "dummy_retry_tool", "depends_on": [], "risk_level": "LOW"}], "verification_requirements": []}
    db_session.add(step)
    await db_session.commit()
    step_id = step.id

    await orchestrator.run_task(task_id)

    # Step should be COMPLETED after 1 retry
    async with TestingSessionLocal() as session:
        res = await session.execute(select(TaskStep).where(TaskStep.id == step_id))
        updated_step = res.scalar_one()
    assert updated_step.status == "COMPLETED"
    assert updated_step.retry_count == 1

@pytest.mark.asyncio
async def test_orchestrator_retry_exhaustion_failure(db_session):
    user = User(email="fail_user@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = Task(user_id=user.id, goal="Test failure flow", status="RUNNING")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task_id = task.id

    step = TaskStep(
        task_id=task_id,
        step_number=1,
        step_key="step_1",
        description="Run failing tool",
        tool_name="dummy_always_fail_tool",
        depends_on=[],
        input_hints={"val": "fail"},
        risk_level="LOW",
        status="PENDING"
    )
    task.plan = {"goal": "Test failure flow", "steps": [{"id": "step_1", "description": "Run failing tool", "tool": "dummy_always_fail_tool", "depends_on": [], "risk_level": "LOW"}], "verification_requirements": []}
    db_session.add(step)
    await db_session.commit()

    await orchestrator.run_task(task_id)

    async with TestingSessionLocal() as session:
        res = await session.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task_id))
        failed_task = res.scalar_one()
    assert failed_task.status == "FAILED"
    assert failed_task.steps[0].status == "FAILED"

@pytest.mark.asyncio
async def test_orchestrator_high_risk_pause_and_approval(db_session):
    user = User(email="approval_user@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = Task(user_id=user.id, goal="Draft and send email notification", status="PENDING")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task_id = task.id

    # Run task - mock LLM will generate plan with email_send (HIGH risk)
    await orchestrator.run_task(task_id)

    async with TestingSessionLocal() as session:
        res = await session.execute(
            select(Task)
            .options(selectinload(Task.steps), selectinload(Task.approvals))
            .where(Task.id == task_id)
        )
        paused_task = res.scalar_one()
        approvals = list(paused_task.approvals)

    # Task pauses at WAITING_APPROVAL
    assert paused_task.status == "WAITING_APPROVAL"
    assert len(approvals) >= 1
    approval = approvals[0]
    approval_id = approval.id
    assert approval.status == "PENDING"
    assert approval.risk_level == "HIGH"

    # Simulate approval
    ok = await orchestrator.handle_approval(task_id, approval_id, approved=True)
    assert ok is True

    # Await background task execution
    bg = orchestrator._running_tasks.get(str(task_id))
    if bg:
        await bg
    else:
        await asyncio.sleep(0.6)

    async with TestingSessionLocal() as session:
        res_resumed = await session.execute(select(Task).where(Task.id == task_id))
        resumed_task = res_resumed.scalar_one()
    assert resumed_task.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "RUNNING")

@pytest.mark.asyncio
async def test_orchestrator_cancel(db_session):
    user = User(email="cancel_user@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = Task(user_id=user.id, goal="Task to be cancelled", status="RUNNING")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    task_id = task.id

    cancelled = await orchestrator.cancel_task(task_id)
    assert cancelled is True

    async with TestingSessionLocal() as session:
        res = await session.execute(select(Task).where(Task.id == task_id))
        cancelled_task = res.scalar_one()
    assert cancelled_task.status == "CANCELLED"
