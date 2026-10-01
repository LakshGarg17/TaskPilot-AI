from typing import List, Dict, Any, Tuple
from app.core.logging import logger
from app.core.errors import TaskPilotError
from app.services.llm.base import LLMProvider
from app.schemas.plan import PlanSchema, PlanStep
from app.agents.tools.registry import tool_registry
import app.agents.tools  # Ensure tools are loaded in registry

def validate_plan_dag(steps: List[PlanStep]) -> Tuple[bool, List[str]]:
    errors = []
    step_ids = [s.id for s in steps]

    # 1. Unique IDs
    if len(step_ids) != len(set(step_ids)):
        errors.append("Duplicate step IDs found in plan.")

    id_set = set(step_ids)

    # 2. Tools exist in registry & dependency validity
    for s in steps:
        tool = tool_registry.get(s.tool)
        if not tool:
            errors.append(f"Step '{s.id}' references unknown tool '{s.tool}'. Available tools: {[t.name for t in tool_registry.list_tools()]}")
        else:
            # Enforce HIGH risk level if tool is HIGH risk
            if tool.risk_level == "HIGH" and s.risk_level != "HIGH":
                s.risk_level = "HIGH"

        for dep in s.depends_on:
            if dep == s.id:
                errors.append(f"Step '{s.id}' cannot depend on itself.")
            elif dep not in id_set:
                errors.append(f"Step '{s.id}' depends on non-existent step '{dep}'.")

    # 3. Cycle detection in DAG (DFS: 0=unvisited, 1=visiting, 2=visited)
    adj: Dict[str, List[str]] = {s.id: list(s.depends_on) for s in steps}
    visited: Dict[str, int] = {sid: 0 for sid in id_set}

    def has_cycle(node: str) -> bool:
        visited[node] = 1  # visiting
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                continue
            if visited[neighbor] == 1:
                return True
            if visited[neighbor] == 0:
                if has_cycle(neighbor):
                    return True
        visited[node] = 2  # visited
        return False

    for sid in id_set:
        if visited[sid] == 0:
            if has_cycle(sid):
                errors.append("Cyclic dependency detected among plan steps.")
                break

    return len(errors) == 0, errors


class Planner:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def create_plan(self, goal: str, max_repairs: int = 2) -> PlanSchema:
        available_tools = tool_registry.get_descriptions()
        tools_summary = "\n".join([
            f"- {t['name']}: {t['description']} (Risk Level: {t['risk_level']})"
            for t in available_tools
        ])

        system_prompt = (
            "You are an expert autonomous AI workflow planner. Your job is to break down a high-level user goal into a minimal, "
            "executable Directed Acyclic Graph (DAG) of discrete steps using ONLY the available tools.\n\n"
            f"AVAILABLE TOOLS:\n{tools_summary}\n\n"
            "PLANNING RULES:\n"
            "1. Each step must have a unique id (e.g. 'step_1', 'step_2').\n"
            "2. 'tool' MUST be one of the available tool names exactly.\n"
            "3. 'depends_on' must be a list of step IDs that MUST complete before this step. No cycles!\n"
            "4. 'risk_level' must be LOW, MEDIUM, or HIGH. If 'email_send' is used, risk_level MUST be HIGH.\n"
            "5. 'input_hints' must provide relevant keywords, queries, or arguments for that tool.\n"
            "6. Provide a list of 'verification_requirements' checking goal completeness.\n"
            "7. Output valid RFC8259 JSON only conforming to the schema:\n"
            "{\n"
            "  \"goal\": string,\n"
            "  \"steps\": [\n"
            "    {\"id\": string, \"description\": string, \"tool\": string, \"depends_on\": [string], \"input_hints\": object, \"expected_output\": string, \"risk_level\": \"LOW\"|\"MEDIUM\"|\"HIGH\"}\n"
            "  ],\n"
            "  \"verification_requirements\": [string]\n"
            "}"
        )

        prompt = f"Goal to accomplish:\n{goal}"
        attempt = 0
        last_errors = []

        while attempt <= max_repairs:
            current_prompt = prompt
            if attempt > 0 and last_errors:
                current_prompt += f"\n\nCRITICAL FIX: Your previous generated plan failed validation with the following errors:\n"
                for err in last_errors:
                    current_prompt += f"- {err}\n"
                current_prompt += "Please repair the plan and return a corrected valid JSON plan with no cycles and only valid tools."

            try:
                raw_data = await self.llm.complete_json(
                    prompt=current_prompt,
                    system_prompt=system_prompt,
                    schema=PlanSchema
                )
                plan = PlanSchema.model_validate(raw_data)
                is_valid, errors = validate_plan_dag(plan.steps)
                if is_valid:
                    return plan

                logger.warning(f"Plan validation failed (attempt {attempt + 1}/{max_repairs + 1}): {errors}")
                last_errors = errors
            except Exception as e:
                logger.warning(f"Plan generation failed (attempt {attempt + 1}/{max_repairs + 1}): {e}")
                last_errors = [str(e)]

            attempt += 1

        raise TaskPilotError(
            f"Failed to generate a valid plan after {max_repairs + 1} attempts. Errors: {'; '.join(last_errors)}",
            status_code=422
        )
