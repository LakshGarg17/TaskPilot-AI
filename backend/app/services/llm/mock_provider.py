import json
import asyncio
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from app.services.llm.base import LLMProvider, LLMInvalidJSONError

class MockLLMProvider(LLMProvider):
    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.model_name = model_name

    async def complete_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        timeout: float = 60.0
    ) -> str:
        await asyncio.sleep(0.05)  # brief realistic async delay
        prompt_lower = prompt.lower()
        if "summarize" in prompt_lower:
            return (
                "[MOCK DATA] Summary:\n"
                "• Key AI hackathons include Global AI Builders, Autonomous Agents Hackathon, and Frontier Models Sprint.\n"
                "• Deadlines range from mid-October to late November with prize pools up to $100,000.\n"
                "• Requirements include functional prototypes with public GitHub repositories."
            )
        elif "email" in prompt_lower or "draft" in prompt_lower:
            return (
                "[MOCK DATA]\n"
                "Subject: Hackathon Research & Action Plan\n\n"
                "Hi Team,\n\n"
                "I have completed our deep dive into upcoming top AI hackathons. We identified 3 high-impact competitions with combined prize pools exceeding $150,000.\n\n"
                "Best regards,\nTaskPilot Agent"
            )
        return f"[MOCK DATA] Simulated LLM response for: {prompt[:120]}..."

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        user_prompt = prompt.lower()
        combined = (prompt + " " + (system_prompt or "")).lower()
        prompt_lower = combined
        schema_name = getattr(schema, "__name__", "")

        # Check if caller is asking for a Plan
        if schema_name == "PlanSchema" or "plan" in combined or "steps" in combined or "verification_requirements" in combined:
            # Deterministic plan based on user prompt keywords
            if "email" in user_prompt or "send" in user_prompt:
                data = {
                    "goal": "[MOCK DATA] Plan for email and research task",
                    "steps": [
                        {
                            "id": "step_1",
                            "description": "Search for top AI hackathons and current competition info",
                            "tool": "web_search",
                            "depends_on": [],
                            "input_hints": {"query": "top AI hackathons 2026 deadlines prizes"},
                            "expected_output": "Search result snippets with hackathon details",
                            "risk_level": "LOW"
                        },
                        {
                            "id": "step_2",
                            "description": "Synthesize and draft an email summary of the findings",
                            "tool": "email_draft",
                            "depends_on": ["step_1"],
                            "input_hints": {"recipient": "team@example.com", "subject": "Upcoming AI Hackathons Overview"},
                            "expected_output": "Structured email draft",
                            "risk_level": "MEDIUM"
                        },
                        {
                            "id": "step_3",
                            "description": "Dispatch the finalized email notification to the team",
                            "tool": "email_send",
                            "depends_on": ["step_2"],
                            "input_hints": {"to": "team@example.com", "subject": "Upcoming AI Hackathons Overview"},
                            "expected_output": "Email dispatch status confirmation",
                            "risk_level": "HIGH"
                        }
                    ],
                    "verification_requirements": [
                        "At least 2 sources cited",
                        "Email draft contains hackathon names and deadlines",
                        "High-risk action confirmed before sending"
                    ]
                }
            elif "calculate" in user_prompt or "analyze" in user_prompt or "math" in user_prompt:
                data = {
                    "goal": "[MOCK DATA] Plan for data analysis and computation",
                    "steps": [
                        {
                            "id": "step_1",
                            "description": "Search for benchmark figures and statistical data",
                            "tool": "web_search",
                            "depends_on": [],
                            "input_hints": {"query": "model latency benchmark ms"},
                            "expected_output": "Benchmark latency numbers",
                            "risk_level": "LOW"
                        },
                        {
                            "id": "step_2",
                            "description": "Compute statistical metrics over collected figures",
                            "tool": "calculator",
                            "depends_on": ["step_1"],
                            "input_hints": {"expression": "mean([120, 145, 98, 110, 130])"},
                            "expected_output": "Calculated average latency",
                            "risk_level": "LOW"
                        },
                        {
                            "id": "step_3",
                            "description": "Summarize statistical findings into actionable insights",
                            "tool": "summarize",
                            "depends_on": ["step_2"],
                            "input_hints": {"focus": "performance"},
                            "expected_output": "Executive summary with metrics",
                            "risk_level": "LOW"
                        }
                    ],
                    "verification_requirements": [
                        "Calculated value verified",
                        "Summary incorporates numeric figures"
                    ]
                }
            else:
                # Standard research and report plan
                data = {
                    "goal": "[MOCK DATA] Plan for research, extraction and synthesis",
                    "steps": [
                        {
                            "id": "step_1",
                            "description": "Search for top AI hackathons accepting applications",
                            "tool": "web_search",
                            "depends_on": [],
                            "input_hints": {"query": "top AI hackathons accepting applications 2026 deadlines prizes"},
                            "expected_output": "List of hackathons with URLs and summaries",
                            "risk_level": "LOW"
                        },
                        {
                            "id": "step_2",
                            "description": "Extract structured details regarding prizes, dates, and tracks",
                            "tool": "structured_extract",
                            "depends_on": ["step_1"],
                            "input_hints": {"fields": ["name", "deadline", "prize_pool", "requirements"]},
                            "expected_output": "Structured JSON comparison table",
                            "risk_level": "LOW"
                        },
                        {
                            "id": "step_3",
                            "description": "Generate comprehensive executive synthesis and comparison",
                            "tool": "summarize",
                            "depends_on": ["step_2"],
                            "input_hints": {"format": "report"},
                            "expected_output": "Detailed markdown report with comparison table",
                            "risk_level": "LOW"
                        }
                    ],
                    "verification_requirements": [
                        "Valid sources present",
                        "Non-empty structured table",
                        "Clear comparison of deadlines and prizes"
                    ]
                }

        # Check if caller is asking for verification check
        elif "verification" in prompt_lower or "consistency" in prompt_lower or "checks" in prompt_lower:
            data = {
                "passed": True,
                "checks": [
                    {"name": "goal_alignment", "passed": True, "detail": "[MOCK DATA] Results directly satisfy user prompt."},
                    {"name": "source_grounding", "passed": True, "detail": "[MOCK DATA] Valid external references present."},
                    {"name": "completeness", "passed": True, "detail": "[MOCK DATA] All required comparison fields covered."}
                ]
            }

        # Check if structured extraction
        elif "structured" in prompt_lower or "extract" in prompt_lower:
            data = {
                "items": [
                    {"name": "Global AI Hackathon 2026", "deadline": "Nov 15, 2026", "prize_pool": "$100,000", "focus": "Autonomous Agents"},
                    {"name": "Frontier Models Sprint", "deadline": "Dec 01, 2026", "prize_pool": "$50,000", "focus": "Multimodal Applications"},
                    {"name": "Open Source LLM Cup", "deadline": "Dec 20, 2026", "prize_pool": "$25,000", "focus": "Local Edge Inference"}
                ]
            }

        else:
            data = {
                "result": f"[MOCK DATA] Structured JSON response for prompt: {prompt[:80]}..."
            }

        if schema:
            try:
                validated = schema.model_validate(data)
                return validated.model_dump()
            except Exception as ve:
                raise LLMInvalidJSONError(f"Mock validation failed: {ve}")
        return data
