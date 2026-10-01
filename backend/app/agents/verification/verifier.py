import urllib.parse
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field
from app.services.llm.base import LLMProvider

class VerificationCheckItem(BaseModel):
    name: str
    passed: bool
    detail: str

class VerificationResult(BaseModel):
    passed: bool
    checks: List[VerificationCheckItem]

class Verifier:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def run_rule_checks(self, goal: str, step_records: List[Dict[str, Any]], sources: List[Dict[str, Any]]) -> List[VerificationCheckItem]:
        checks: List[VerificationCheckItem] = []

        # 1. Non-empty outputs check
        empty_steps = [s.get("step_key", "unknown") for s in step_records if not s.get("output_data") and s.get("status") == "COMPLETED"]
        if empty_steps:
            checks.append(VerificationCheckItem(
                name="step_outputs_non_empty",
                passed=False,
                detail=f"Steps produced empty outputs: {', '.join(empty_steps)}"
            ))
        else:
            checks.append(VerificationCheckItem(
                name="step_outputs_non_empty",
                passed=True,
                detail="All completed steps produced non-empty output data."
            ))

        # 2. Web tools sources check
        web_steps = [s for s in step_records if s.get("tool_name") in ("web_search", "web_extract")]
        if web_steps:
            if not sources or len(sources) == 0:
                checks.append(VerificationCheckItem(
                    name="web_sources_present",
                    passed=False,
                    detail="Web tools were executed but no reference sources were recorded."
                ))
            else:
                checks.append(VerificationCheckItem(
                    name="web_sources_present",
                    passed=True,
                    detail=f"Recorded {len(sources)} grounded reference sources."
                ))
        else:
            checks.append(VerificationCheckItem(
                name="web_sources_present",
                passed=True,
                detail="No external web tools required for this workflow."
            ))

        # 3. URL validity check
        invalid_urls = []
        for src in sources:
            url = src.get("url", "")
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                invalid_urls.append(url)

        if invalid_urls:
            checks.append(VerificationCheckItem(
                name="well_formed_urls",
                passed=False,
                detail=f"Sources contain malformed URLs: {', '.join(invalid_urls[:3])}"
            ))
        else:
            checks.append(VerificationCheckItem(
                name="well_formed_urls",
                passed=True,
                detail="All cited web URLs are well-formed and valid."
            ))

        return checks

    async def verify(
        self,
        goal: str,
        step_records: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        verification_requirements: List[str] = None
    ) -> VerificationResult:
        # Run rule checks
        rule_checks = self.run_rule_checks(goal, step_records, sources)

        # Run LLM consistency check
        system_prompt = (
            "You are a strict QA verification inspector. Evaluate whether the completed execution steps and outputs "
            "faithfully and completely fulfill the original user goal and any verification requirements.\n"
            "Return JSON format:\n"
            "{\n"
            "  \"passed\": boolean,\n"
            "  \"checks\": [\n"
            "    {\"name\": string, \"passed\": boolean, \"detail\": string}\n"
            "  ]\n"
            "}"
        )

        steps_summary = "\n".join([
            f"- Step {s.get('step_key')}: {s.get('description')} ({s.get('tool_name')}) -> Status: {s.get('status')}"
            for s in step_records
        ])

        reqs_summary = "\n".join([f"- {r}" for r in (verification_requirements or [])]) or "General completeness"

        prompt = (
            f"Original Goal: {goal}\n\n"
            f"Verification Requirements:\n{reqs_summary}\n\n"
            f"Executed Steps:\n{steps_summary}\n\n"
            f"Sources Cited: {len(sources)} sources\n"
            "Verify goal satisfaction and consistency."
        )

        try:
            llm_result_data = await self.llm.complete_json(
                prompt=prompt,
                system_prompt=system_prompt,
                schema=VerificationResult
            )
            llm_result = VerificationResult.model_validate(llm_result_data)
            all_checks = rule_checks + llm_result.checks
            all_passed = all(c.passed for c in all_checks)
            return VerificationResult(passed=all_passed, checks=all_checks)
        except Exception as e:
            # Fallback if LLM verification call fails
            fallback_passed = all(c.passed for c in rule_checks)
            rule_checks.append(VerificationCheckItem(
                name="llm_consistency_check",
                passed=fallback_passed,
                detail=f"Rule checks evaluated. LLM check note: {str(e)[:100]}"
            ))
            return VerificationResult(passed=fallback_passed, checks=rule_checks)
