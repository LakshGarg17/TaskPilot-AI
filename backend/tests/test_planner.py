import pytest
from app.agents.planner.planner import Planner, validate_plan_dag
from app.schemas.plan import PlanStep, PlanSchema
from app.services.llm.mock_provider import MockLLMProvider
from app.core.errors import TaskPilotError

@pytest.mark.asyncio
async def test_validate_plan_valid():
    steps = [
        PlanStep(
            id="step_1",
            description="Search for info",
            tool="web_search",
            depends_on=[],
            risk_level="LOW"
        ),
        PlanStep(
            id="step_2",
            description="Summarize findings",
            tool="summarize",
            depends_on=["step_1"],
            risk_level="LOW"
        )
    ]
    is_valid, errors = validate_plan_dag(steps)
    assert is_valid is True
    assert len(errors) == 0

@pytest.mark.asyncio
async def test_validate_plan_unknown_tool():
    steps = [
        PlanStep(
            id="step_1",
            description="Run arbitrary bash",
            tool="arbitrary_bash_shell",
            depends_on=[],
            risk_level="HIGH"
        )
    ]
    is_valid, errors = validate_plan_dag(steps)
    assert is_valid is False
    assert any("unknown tool" in e for e in errors)

@pytest.mark.asyncio
async def test_validate_plan_cyclic_dependencies():
    steps = [
        PlanStep(
            id="step_1",
            description="Step 1",
            tool="web_search",
            depends_on=["step_2"],
            risk_level="LOW"
        ),
        PlanStep(
            id="step_2",
            description="Step 2",
            tool="summarize",
            depends_on=["step_1"],
            risk_level="LOW"
        )
    ]
    is_valid, errors = validate_plan_dag(steps)
    assert is_valid is False
    assert any("Cyclic dependency" in e for e in errors)

@pytest.mark.asyncio
async def test_planner_create_plan_with_mock():
    planner = Planner(MockLLMProvider())
    plan = await planner.create_plan("Research top AI hackathons and summarize")
    assert isinstance(plan, PlanSchema)
    assert len(plan.steps) >= 2
    assert plan.steps[0].id == "step_1"
    is_valid, errors = validate_plan_dag(plan.steps)
    assert is_valid is True

@pytest.mark.asyncio
async def test_planner_repair_retry():
    # A mock provider that fails once with invalid JSON then succeeds
    class FlakyMockLLM(MockLLMProvider):
        def __init__(self):
            super().__init__()
            self.calls = 0

        async def complete_json(self, prompt, system_prompt=None, schema=None, **kwargs):
            self.calls += 1
            if self.calls == 1:
                # Return plan with cyclic dependency
                return {
                    "goal": "Test goal",
                    "steps": [
                        {"id": "step_1", "description": "1", "tool": "web_search", "depends_on": ["step_2"], "risk_level": "LOW"},
                        {"id": "step_2", "description": "2", "tool": "summarize", "depends_on": ["step_1"], "risk_level": "LOW"}
                    ],
                    "verification_requirements": []
                }
            # On repair attempt, return valid plan
            return await super().complete_json(prompt, system_prompt, schema, **kwargs)

    flaky_llm = FlakyMockLLM()
    planner = Planner(flaky_llm)
    plan = await planner.create_plan("Research hackathons", max_repairs=2)
    assert flaky_llm.calls == 2
    assert isinstance(plan, PlanSchema)
