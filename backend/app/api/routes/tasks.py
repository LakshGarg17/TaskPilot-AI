import asyncio
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.database.session import get_db, AsyncSessionLocal
from app.models import User, Task, TaskStep, TaskEvent, Approval
from app.schemas.tasks import (
    TaskCreate, TaskResponse, TaskStepResponse, EventResponse, ApprovalDecision
)
from app.api.deps import get_current_user, rate_limit
from app.agents.orchestrator.orchestrator import orchestrator
from app.services.event_bus import event_bus

router = APIRouter(prefix="/tasks", tags=["Tasks"])

TERMINAL_EVENTS = {"TASK_COMPLETED", "TASK_FAILED", "TASK_CANCELLED"}

@router.post("", response_model=TaskResponse, dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))])
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = Task(
        user_id=current_user.id,
        goal=task_in.goal.strip(),
        status="PENDING"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Launch background orchestrator
    orchestrator.start_task(task.id)

    # Return initial task state
    res = await db.execute(
        select(Task)
        .options(
            selectinload(Task.steps),
            selectinload(Task.tool_executions),
            selectinload(Task.result),
            selectinload(Task.approvals)
        )
        .where(Task.id == task.id)
    )
    return res.scalar_one()


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Task)
        .options(
            selectinload(Task.steps),
            selectinload(Task.tool_executions),
            selectinload(Task.result),
            selectinload(Task.approvals)
        )
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
    )
    return res.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Task)
        .options(
            selectinload(Task.steps),
            selectinload(Task.tool_executions),
            selectinload(Task.result),
            selectinload(Task.approvals)
        )
        .where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await orchestrator.cancel_task(task_id)
    return {"message": "Task cancelled successfully"}


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Find pending approval for this task
    res = await db.execute(
        select(Approval).where(
            Approval.task_id == task_id,
            Approval.user_id == current_user.id,
            Approval.status == "PENDING"
        )
    )
    approval = res.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=400, detail="No pending approval for this task")

    success = await orchestrator.handle_approval(task_id, approval.id, approved=True)
    return {"message": "Action approved. Workflow resumed.", "success": success}


@router.post("/{task_id}/reject")
async def reject_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Approval).where(
            Approval.task_id == task_id,
            Approval.user_id == current_user.id,
            Approval.status == "PENDING"
        )
    )
    approval = res.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=400, detail="No pending approval for this task")

    success = await orchestrator.handle_approval(task_id, approval.id, approved=False)
    return {"message": "Action rejected. Step skipped.", "success": success}


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Reset any failed steps to PENDING
    failed_steps = [s for s in task.steps if s.status == "FAILED"]
    for s in failed_steps:
        s.status = "PENDING"
        s.retry_count = 0
        s.error_message = None

    task.status = "RUNNING"
    task.error_message = None
    task.completed_at = None
    await db.commit()

    orchestrator.start_task(task_id)
    return {"message": "Task retry initiated"}


@router.get("/{task_id}/events")
async def stream_task_events(
    task_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Enforce ownership
    task_res = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    last_event_id = request.headers.get("Last-Event-ID")

    async def event_generator():
        # 1. Replay historical events from DB
        async with AsyncSessionLocal() as session:
            query = select(TaskEvent).where(TaskEvent.task_id == task_id).order_by(TaskEvent.created_at.asc())
            events_res = await session.execute(query)
            historical_events = list(events_res.scalars().all())

        replayed_ids = set()
        seen_terminal = False

        skip = bool(last_event_id)
        for ev in historical_events:
            ev_id_str = str(ev.id)
            if skip:
                if ev_id_str == last_event_id:
                    skip = False
                continue

            replayed_ids.add(ev_id_str)
            data_payload = {
                "id": ev_id_str,
                "task_id": str(ev.task_id),
                "event_type": ev.event_type,
                "step_id": ev.step_id,
                "tool": ev.tool,
                "message": ev.message,
                "payload": ev.payload,
                "created_at": ev.created_at.isoformat()
            }
            yield f"id: {ev_id_str}\nevent: {ev.event_type}\ndata: {json.dumps(data_payload)}\n\n"
            if ev.event_type in TERMINAL_EVENTS:
                seen_terminal = True

        if seen_terminal:
            return

        # 2. Subscribe to live events via EventBus
        queue = await event_bus.subscribe(str(task_id))
        try:
            while True:
                # Disconnect check
                if await request.is_disconnected():
                    break

                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    ev_id = event_data.get("id")
                    if ev_id in replayed_ids:
                        continue

                    ev_type = event_data.get("event_type", "message")
                    yield f"id: {ev_id}\nevent: {ev_type}\ndata: {json.dumps(event_data)}\n\n"

                    if ev_type in TERMINAL_EVENTS:
                        break

                except asyncio.TimeoutError:
                    # Heartbeat comment to keep connection alive
                    yield ": ping\n\n"

        finally:
            await event_bus.unsubscribe(str(task_id), queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
