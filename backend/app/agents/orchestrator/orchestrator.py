import asyncio
import datetime
import time
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.database.session import AsyncSessionLocal
from app.models import Task, TaskStep, ToolExecution, TaskResult, Approval, TaskEvent
from app.services.event_bus import event_bus
from app.services.llm import get_llm_provider
from app.services.search import get_search_provider
from app.agents.planner.planner import Planner
from app.agents.verification.verifier import Verifier
from app.agents.tools.registry import tool_registry
import app.agents.tools  # Ensure tools are loaded

class Orchestrator:
    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def emit_event(
        self,
        task_id: uuid.UUID,
        event_type: str,
        message: str,
        step_id: Optional[str] = None,
        tool: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = payload or {}
        now = datetime.datetime.now(datetime.timezone.utc)
        event_id = uuid.uuid4()

        event_dict = {
            "id": str(event_id),
            "task_id": str(task_id),
            "event_type": event_type,
            "step_id": step_id,
            "tool": tool,
            "message": message,
            "payload": payload,
            "created_at": now.isoformat()
        }

        # Persist event in fresh DB session
        async with AsyncSessionLocal() as session:
            db_event = TaskEvent(
                id=event_id,
                task_id=task_id,
                event_type=event_type,
                step_id=step_id,
                tool=tool,
                message=message,
                payload=payload,
                created_at=now
            )
            session.add(db_event)
            await session.commit()

        # Publish to live subscribers
        await event_bus.publish(str(task_id), event_dict)
        return event_dict

    def start_task(self, task_id: uuid.UUID):
        """Launches the task in background asyncio loop"""
        task_str = str(task_id)
        bg_task = asyncio.create_task(self.run_task(task_id))
        self._running_tasks[task_str] = bg_task

        def _cleanup(t):
            self._running_tasks.pop(task_str, None)

        bg_task.add_done_callback(_cleanup)

    async def cancel_task(self, task_id: uuid.UUID) -> bool:
        task_str = str(task_id)
        if task_str in self._running_tasks:
            self._running_tasks[task_str].cancel()

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task and task.status not in ("COMPLETED", "FAILED", "CANCELLED"):
                task.status = "CANCELLED"
                task.completed_at = datetime.datetime.now(datetime.timezone.utc)
                await session.commit()

        await self.emit_event(
            task_id=task_id,
            event_type="TASK_CANCELLED",
            message="Task was manually cancelled by the user."
        )
        return True

    async def run_task(self, task_id: uuid.UUID, resume_step_key: Optional[str] = None):
        """Main execution workflow: Understand -> Plan -> Execute -> Verify -> Result"""
        llm = get_llm_provider()
        search_prov = get_search_provider()

        # Step 1: Initialize Task
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
            )
            task = res.scalar_one_or_none()
            if not task:
                logger.error(f"Task {task_id} not found")
                return

            goal = task.goal
            existing_plan = task.plan

        if not resume_step_key:
            await self.emit_event(
                task_id=task_id,
                event_type="TASK_STARTED",
                message=f"Task initiated: '{goal[:80]}...'. Initializing autonomous planner."
            )

        # Step 2: Planning (if not already planned)
        plan_data = existing_plan
        if not plan_data:
            async with AsyncSessionLocal() as session:
                await session.execute(update(Task).where(Task.id == task_id).values(status="PLANNING"))
                await session.commit()

            planner = Planner(llm)
            try:
                plan = await planner.create_plan(goal)
                plan_data = plan.model_dump()

                async with AsyncSessionLocal() as session:
                    task_update = await session.execute(select(Task).where(Task.id == task_id))
                    t = task_update.scalar_one()
                    t.plan = plan_data
                    t.status = "RUNNING"

                    # Create TaskStep rows
                    for idx, step in enumerate(plan.steps, start=1):
                        db_step = TaskStep(
                            task_id=task_id,
                            step_number=idx,
                            step_key=step.id,
                            description=step.description,
                            tool_name=step.tool,
                            depends_on=step.depends_on,
                            input_hints=step.input_hints,
                            expected_output=step.expected_output,
                            risk_level=step.risk_level,
                            status="PENDING"
                        )
                        session.add(db_step)
                    await session.commit()

                await self.emit_event(
                    task_id=task_id,
                    event_type="PLAN_CREATED",
                    message=f"Formulated validated execution DAG with {len(plan.steps)} steps and {len(plan.verification_requirements)} verification requirements.",
                    payload={"plan": plan_data}
                )

            except Exception as e:
                logger.exception(f"Planning failed for task {task_id}")
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(Task).where(Task.id == task_id).values(
                            status="FAILED",
                            error_message=f"Planning failed: {str(e)}",
                            completed_at=datetime.datetime.now(datetime.timezone.utc)
                        )
                    )
                    await session.commit()

                await self.emit_event(
                    task_id=task_id,
                    event_type="TASK_FAILED",
                    message=f"Planning failed: {str(e)}"
                )
                return

        # Step 3: Execution Loop
        tool_context = {
            "llm_provider": llm,
            "search_provider": search_prov,
            "task_id": task_id
        }

        while True:
            # Check for cancellation or status
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
                )
                task = res.scalar_one_or_none()
                if not task or task.status == "CANCELLED":
                    return

                steps = list(task.steps)

            completed_keys = {s.step_key for s in steps if s.status in ("COMPLETED", "SKIPPED")}
            failed_steps = [s for s in steps if s.status == "FAILED"]
            if failed_steps:
                # Terminal failure
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(Task).where(Task.id == task_id).values(
                            status="FAILED",
                            error_message=f"Step {failed_steps[0].step_key} failed: {failed_steps[0].error_message}",
                            completed_at=datetime.datetime.now(datetime.timezone.utc)
                        )
                    )
                    await session.commit()
                await self.emit_event(
                    task_id=task_id,
                    event_type="TASK_FAILED",
                    message=f"Execution halted: step {failed_steps[0].step_key} failed."
                )
                return

            # Check if all steps are completed
            if len(completed_keys) == len(steps):
                break

            # Find next runnable step
            ready_step = None
            for s in steps:
                if s.status == "PENDING":
                    # Check if all dependencies are satisfied
                    if all(dep in completed_keys for dep in s.depends_on):
                        ready_step = s
                        break
                elif s.status == "WAITING_APPROVAL":
                    # Paused waiting for approval
                    return

            if not ready_step:
                logger.error(f"Deadlock or unresolvable dependencies for task {task_id}")
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(Task).where(Task.id == task_id).values(
                            status="FAILED",
                            error_message="Dependency resolution stalled (deadlock detected)",
                            completed_at=datetime.datetime.now(datetime.timezone.utc)
                        )
                    )
                    await session.commit()
                return

            # Check approval risk policy
            step_key = ready_step.step_key
            tool_name = ready_step.tool_name
            tool_inst = tool_registry.get(tool_name)
            is_high_risk = ready_step.risk_level == "HIGH" or (tool_inst and tool_inst.risk_level == "HIGH")

            # Check if this step was already approved by the user
            async with AsyncSessionLocal() as session:
                res_app = await session.execute(
                    select(Approval).where(
                        Approval.step_id == ready_step.id,
                        Approval.status == "APPROVED"
                    )
                )
                is_already_approved = res_app.scalar_one_or_none() is not None

            if is_high_risk and not is_already_approved:
                # Pause and request approval
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(TaskStep).where(TaskStep.id == ready_step.id).values(status="WAITING_APPROVAL")
                    )
                    await session.execute(
                        update(Task).where(Task.id == task_id).values(status="WAITING_APPROVAL")
                    )
                    # Create Approval record
                    action_summary = f"Execute high-impact tool '{tool_name}' for step {step_key}: {ready_step.description}"
                    approval = Approval(
                        task_id=task_id,
                        step_id=ready_step.id,
                        user_id=task.user_id,
                        tool_name=tool_name,
                        action_summary=action_summary,
                        inputs=ready_step.input_hints,
                        risk_level="HIGH",
                        status="PENDING"
                    )
                    session.add(approval)
                    await session.commit()
                    approval_id = approval.id

                await self.emit_event(
                    task_id=task_id,
                    event_type="APPROVAL_REQUIRED",
                    step_id=step_key,
                    tool=tool_name,
                    message=f"Human approval required: {action_summary}",
                    payload={"approval_id": str(approval_id), "step_id": step_key, "tool": tool_name}
                )
                return  # Halts execution until resume via approve/reject endpoint

            # Execute the ready step
            success = await self._execute_step(task_id, ready_step, steps, tool_context)
            if not success:
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(Task).where(Task.id == task_id).values(
                            status="FAILED",
                            error_message=f"Step '{step_key}' failed after retry exhaustion.",
                            completed_at=datetime.datetime.now(datetime.timezone.utc)
                        )
                    )
                    await session.commit()
                await self.emit_event(
                    task_id=task_id,
                    event_type="TASK_FAILED",
                    message=f"Execution halted: step '{step_key}' failed after retry exhaustion."
                )
                return

        # Step 4: Verification Phase
        async with AsyncSessionLocal() as session:
            await session.execute(update(Task).where(Task.id == task_id).values(status="VERIFYING"))
            await session.commit()

        await self.emit_event(
            task_id=task_id,
            event_type="VERIFICATION_STARTED",
            message="Commencing verification: running structural rule checks and LLM consistency evaluation."
        )

        verifier = Verifier(llm)
        async with AsyncSessionLocal() as session:
            res_steps = await session.execute(
                select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.step_number)
            )
            all_db_steps = list(res_steps.scalars().all())

            res_tools = await session.execute(
                select(ToolExecution).where(ToolExecution.task_id == task_id)
            )
            all_executions = list(res_tools.scalars().all())

        step_records = [
            {
                "step_key": s.step_key,
                "description": s.description,
                "tool_name": s.tool_name,
                "status": s.status,
                "output_data": s.output_data
            }
            for s in all_db_steps
        ]
        all_sources = []
        for ex in all_executions:
            if ex.sources:
                all_sources.extend(ex.sources)

        # De-duplicate sources
        unique_sources = []
        seen_urls = set()
        for s in all_sources:
            url = s.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(s)

        reqs = plan_data.get("verification_requirements", [])
        v_result = await verifier.verify(goal, step_records, unique_sources, reqs)

        await self.emit_event(
            task_id=task_id,
            event_type="VERIFICATION_COMPLETED",
            message=f"Verification complete ({'PASSED' if v_result.passed else 'COMPLETED WITH WARNINGS'}): {len(v_result.checks)} criteria evaluated.",
            payload={"verification_report": v_result.model_dump()}
        )

        # Step 5: Final Result Synthesis
        final_result = await self._synthesize_final_result(
            goal=goal,
            step_records=step_records,
            sources=unique_sources,
            v_result=v_result,
            llm=llm
        )

        final_status = "COMPLETED" if v_result.passed else "COMPLETED_WITH_WARNINGS"
        now = datetime.datetime.now(datetime.timezone.utc)

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Task).where(Task.id == task_id).values(
                    status=final_status,
                    completed_at=now
                )
            )
            # Create or update TaskResult record
            res_existing = await session.execute(select(TaskResult).where(TaskResult.task_id == task_id))
            db_res = res_existing.scalar_one_or_none()
            if not db_res:
                db_res = TaskResult(
                    task_id=task_id,
                    markdown=final_result["markdown"],
                    tables=final_result.get("tables", []),
                    cards=final_result.get("cards", []),
                    chart_data=final_result.get("chart_data"),
                    sources=unique_sources,
                    email_draft=final_result.get("email_draft"),
                    verification_report=v_result.model_dump(),
                    created_at=now
                )
                session.add(db_res)
            else:
                db_res.markdown = final_result["markdown"]
                db_res.tables = final_result.get("tables", [])
                db_res.cards = final_result.get("cards", [])
                db_res.chart_data = final_result.get("chart_data")
                db_res.sources = unique_sources
                db_res.email_draft = final_result.get("email_draft")
                db_res.verification_report = v_result.model_dump()
            await session.commit()

        await self.emit_event(
            task_id=task_id,
            event_type="TASK_COMPLETED",
            message=f"Task completed successfully. Final synthesized report and verification data ready.",
            payload={"result": final_result, "status": final_status}
        )

    async def _execute_step(
        self,
        task_id: uuid.UUID,
        step: TaskStep,
        all_steps: List[TaskStep],
        context: Dict[str, Any]
    ) -> bool:
        step_id = step.id
        step_key = step.step_key
        tool_name = step.tool_name

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(TaskStep).where(TaskStep.id == step_id).values(
                    status="RUNNING",
                    started_at=datetime.datetime.now(datetime.timezone.utc)
                )
            )
            await session.commit()

        await self.emit_event(
            task_id=task_id,
            event_type="STEP_STARTED",
            step_id=step_key,
            tool=tool_name,
            message=f"Initiating step '{step_key}': {step.description}"
        )

        tool = tool_registry.get(tool_name)
        if not tool:
            err = f"Tool '{tool_name}' not found in registry"
            await self._record_step_failure(task_id, step_id, step_key, tool_name, err)
            return False

        # Gather dependency outputs
        step_inputs = dict(step.input_hints or {})
        dep_outputs = {}
        for prev in all_steps:
            if prev.step_key in step.depends_on and prev.output_data:
                dep_outputs[prev.step_key] = prev.output_data

        # Feed previous outputs into inputs if applicable
        if dep_outputs:
            combined_text = []
            for k, out in dep_outputs.items():
                if isinstance(out, dict):
                    if "text" in out:
                        combined_text.append(str(out["text"]))
                    elif "summary" in out:
                        combined_text.append(str(out["summary"]))
                    elif "items" in out:
                        combined_text.append(str(out["items"]))
                    else:
                        combined_text.append(str(out))
                elif isinstance(out, list):
                    # Search results list
                    snippets = [f"- {item.get('title', '')}: {item.get('snippet', '')}" for item in out if isinstance(item, dict)]
                    combined_text.append("\n".join(snippets))

            context_blob = "\n\n".join(combined_text)
            if "text" in tool.input_schema.model_fields and not step_inputs.get("text"):
                step_inputs["text"] = context_blob
            if "context_text" in tool.input_schema.model_fields and not step_inputs.get("context_text"):
                step_inputs["context_text"] = context_blob
            if "body" in tool.input_schema.model_fields and not step_inputs.get("body"):
                for k, out in dep_outputs.items():
                    if isinstance(out, dict) and "body" in out:
                        step_inputs["body"] = out["body"]
                        break
                if not step_inputs.get("body"):
                    step_inputs["body"] = context_blob or "No details provided"
            if "to" in tool.input_schema.model_fields and not step_inputs.get("to"):
                for k, out in dep_outputs.items():
                    if isinstance(out, dict) and ("recipient" in out or "to" in out):
                        step_inputs["to"] = out.get("to") or out.get("recipient")
                        break

        # Retry loop (up to 3 attempts with backoff)
        max_attempts = 3
        delay = 1.0

        for attempt in range(1, max_attempts + 1):
            start_time = time.time()
            await self.emit_event(
                task_id=task_id,
                event_type="TOOL_STARTED",
                step_id=step_key,
                tool=tool_name,
                message=f"Executing tool '{tool_name}' (attempt {attempt}/{max_attempts}) with validated parameters.",
                payload={"inputs": step_inputs, "attempt": attempt}
            )

            try:
                # Per-step timeout of 60 seconds
                tool_res = await asyncio.wait_for(
                    tool.execute(step_inputs, context=context),
                    timeout=60.0
                )
                duration_ms = (time.time() - start_time) * 1000

                # Record execution in DB
                async with AsyncSessionLocal() as session:
                    db_exec = ToolExecution(
                        task_id=task_id,
                        step_id=step_id,
                        tool_name=tool_name,
                        inputs=step_inputs,
                        output=tool_res.data if isinstance(tool_res.data, dict) else {"result": tool_res.data},
                        ok=tool_res.ok,
                        sources=tool_res.sources,
                        duration_ms=duration_ms,
                        attempt=attempt
                    )
                    session.add(db_exec)
                    await session.commit()

                if tool_res.ok:
                    # Step success!
                    async with AsyncSessionLocal() as session:
                        await session.execute(
                            update(TaskStep).where(TaskStep.id == step_id).values(
                                status="COMPLETED",
                                output_data=tool_res.data if isinstance(tool_res.data, dict) else {"result": tool_res.data},
                                completed_at=datetime.datetime.now(datetime.timezone.utc),
                                retry_count=attempt - 1
                            )
                        )
                        await session.commit()

                    await self.emit_event(
                        task_id=task_id,
                        event_type="TOOL_COMPLETED",
                        step_id=step_key,
                        tool=tool_name,
                        message=f"Tool '{tool_name}' completed successfully in {duration_ms:.1f}ms: {tool_res.summary}",
                        payload={"summary": tool_res.summary, "duration_ms": duration_ms}
                    )
                    await self.emit_event(
                        task_id=task_id,
                        event_type="STEP_COMPLETED",
                        step_id=step_key,
                        tool=tool_name,
                        message=f"Step '{step_key}' completed."
                    )
                    return True
                else:
                    # Tool returned ok=False
                    err = tool_res.error or "Tool execution error"
                    logger.warning(f"Step {step_key} attempt {attempt} failed: {err}")
                    if attempt < max_attempts:
                        await self.emit_event(
                            task_id=task_id,
                            event_type="RETRY",
                            step_id=step_key,
                            tool=tool_name,
                            message=f"Tool failed: {err}. Retrying in {delay}s (attempt {attempt + 1}/{max_attempts})."
                        )
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        await self._record_step_failure(task_id, step_id, step_key, tool_name, err)
                        return False

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                err = f"Execution error: {str(e)}"
                logger.warning(f"Step {step_key} attempt {attempt} exception: {err}")
                if attempt < max_attempts:
                    await self.emit_event(
                        task_id=task_id,
                        event_type="RETRY",
                        step_id=step_key,
                        tool=tool_name,
                        message=f"Tool exception: {err}. Retrying in {delay}s (attempt {attempt + 1}/{max_attempts})."
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    await self._record_step_failure(task_id, step_id, step_key, tool_name, err)
                    return False

        return False

    async def _record_step_failure(
        self,
        task_id: uuid.UUID,
        step_id: uuid.UUID,
        step_key: str,
        tool_name: str,
        error_msg: str
    ):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(TaskStep).where(TaskStep.id == step_id).values(
                    status="FAILED",
                    error_message=error_msg,
                    completed_at=datetime.datetime.now(datetime.timezone.utc)
                )
            )
            await session.commit()

        await self.emit_event(
            task_id=task_id,
            event_type="TOOL_FAILED",
            step_id=step_key,
            tool=tool_name,
            message=f"Tool '{tool_name}' failed after retry exhaustion: {error_msg}"
        )

    async def _synthesize_final_result(
        self,
        goal: str,
        step_records: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        v_result: Verifier,
        llm: Any
    ) -> Dict[str, Any]:
        """Synthesizes markdown report, tables, cards, charts, and email draft"""
        # Collect extracted items, emails, summaries
        tables = []
        cards = []
        chart_data = None
        email_draft = None

        for s in step_records:
            out = s.get("output_data") or {}
            tool = s.get("tool_name")
            if tool == "structured_extract" and isinstance(out, dict):
                items = out.get("items", [])
                if items:
                    tables.append({
                        "title": f"Structured Comparison ({s.get('step_key')})",
                        "headers": list(items[0].keys()) if items else [],
                        "rows": items
                    })
            elif tool == "calculator" and isinstance(out, dict):
                cards.append({
                    "title": "Calculated Metric",
                    "value": str(out.get("result", "")),
                    "description": f"Formula: {out.get('expression', '')}"
                })
            elif tool in ("email_draft", "email_send") and isinstance(out, dict):
                email_draft = {
                    "recipient": out.get("recipient") or out.get("to", ""),
                    "subject": out.get("subject", ""),
                    "body": out.get("body") or out.get("body_preview", "")
                }

        # Build markdown report
        sources_md = "\n".join([f"- [{s.get('title', s.get('domain', 'Link'))}]({s.get('url', '#')}) ({s.get('domain', '')})" for s in sources]) or "None"

        # Formulate rich markdown
        report_lines = [
            f"# Mission Report: {goal}",
            "",
            "## Executive Summary",
            f"TaskPilot executed {len(step_records)} autonomous steps to fulfill your request. All dependency constraints and security policies were enforced.",
            "",
            "## Key Findings & Synthesis"
        ]

        for s in step_records:
            out = s.get("output_data") or {}
            if s.get("tool_name") == "summarize" and isinstance(out, dict) and "summary" in out:
                report_lines.append(f"### {s.get('description')}")
                report_lines.append(out["summary"])
                report_lines.append("")

        if tables:
            report_lines.append("## Comparative Breakdown")
            for t in tables:
                headers = t.get("headers", [])
                report_lines.append(f"### {t.get('title')}")
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for r in t.get("rows", []):
                    report_lines.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")
                report_lines.append("")

        if email_draft:
            report_lines.append("## Email Communication")
            report_lines.append(f"**Recipient:** `{email_draft.get('recipient')}`")
            report_lines.append(f"**Subject:** {email_draft.get('subject')}")
            report_lines.append("```text")
            report_lines.append(email_draft.get("body", ""))
            report_lines.append("```")
            report_lines.append("")

        report_lines.append("## Grounded References & Citations")
        report_lines.append(sources_md)

        # Generate sample chart data if numeric table exists
        if tables and tables[0].get("rows"):
            rows = tables[0]["rows"]
            chart_points = []
            for r in rows:
                name = r.get("name") or r.get("title") or "Item"
                # Extract number from prize or cost if possible
                val_str = str(r.get("prize_pool") or r.get("prize") or r.get("score") or "10")
                digits = "".join([c for c in val_str if c.isdigit()])
                val = int(digits) if digits else 100
                chart_points.append({"name": name[:18], "value": val})
            if chart_points:
                chart_data = {
                    "title": "Comparative Prize Pool / Magnitude Analysis",
                    "data": chart_points
                }

        markdown_doc = "\n".join(report_lines)
        return {
            "markdown": markdown_doc,
            "tables": tables,
            "cards": cards,
            "chart_data": chart_data,
            "email_draft": email_draft,
            "sources": sources
        }

    async def handle_approval(self, task_id: uuid.UUID, approval_id: uuid.UUID, approved: bool) -> bool:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(Approval).where(Approval.id == approval_id, Approval.task_id == task_id)
            )
            approval = res.scalar_one_or_none()
            if not approval or approval.status != "PENDING":
                return False

            now = datetime.datetime.now(datetime.timezone.utc)
            approval.status = "APPROVED" if approved else "REJECTED"
            approval.resolved_at = now

            step_res = await session.execute(
                select(TaskStep).where(TaskStep.id == approval.step_id)
            )
            step = step_res.scalar_one()

            if approved:
                step.status = "PENDING"
                step.risk_level = "LOW"  # Approved for execution
                await session.execute(update(Task).where(Task.id == task_id).values(status="RUNNING"))
            else:
                step.status = "SKIPPED"
                step.error_message = "Step rejected by user."
                await session.execute(update(Task).where(Task.id == task_id).values(status="RUNNING"))

            await session.commit()

        await self.emit_event(
            task_id=task_id,
            event_type="APPROVAL_RESOLVED",
            step_id=step.step_key,
            tool=approval.tool_name,
            message=f"Human approval {'granted' if approved else 'denied'}. Resuming workflow execution.",
            payload={"approved": approved, "approval_id": str(approval_id)}
        )

        # Resume task execution
        self.start_task(task_id)
        return True


orchestrator = Orchestrator()

async def cleanup_orphaned_tasks():
    """Startup cleanup: mark orphaned RUNNING or PLANNING tasks as FAILED (interrupted)"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Task).where(Task.status.in_(["RUNNING", "PLANNING", "VERIFYING"]))
        )
        orphaned = result.scalars().all()
        for t in orphaned:
            t.status = "FAILED"
            t.error_message = "Task interrupted due to server reboot"
            t.completed_at = datetime.datetime.now(datetime.timezone.utc)
        if orphaned:
            await session.commit()
            logger.info(f"Cleaned up {len(orphaned)} orphaned running tasks.")
