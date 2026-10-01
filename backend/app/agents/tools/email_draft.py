from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.agents.tools.base import BaseTool, ToolResult
from app.services.llm import get_llm_provider

class EmailDraftInput(BaseModel):
    recipient: str = Field(..., description="Target email recipient or placeholder")
    subject: str = Field(..., description="Subject line for the email")
    context_text: Optional[str] = Field("", description="Information or context to include in the email body")
    tone: Optional[str] = Field("professional", description="Tone of the email (professional, concise, casual)")

class EmailDraftTool(BaseTool):
    name = "email_draft"
    description = "Drafts a polished, well-formatted email based on research findings or provided context."
    risk_level = "MEDIUM"
    input_schema = EmailDraftInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        validated = self.validate_inputs(inputs)
        llm = context.get("llm_provider") if context else None
        if not llm:
            llm = get_llm_provider()

        system_prompt = (
            "You are an executive communications assistant. Draft a crisp, professional email based on the user's requirements. "
            "Return JSON: {'subject': str, 'body': str, 'recipient': str}"
        )
        prompt = (
            f"Recipient: {validated.recipient}\n"
            f"Subject: {validated.subject}\n"
            f"Tone: {validated.tone}\n"
            f"Context / Key Findings:\n{validated.context_text[:5000]}"
        )

        res = await llm.complete_json(prompt=prompt, system_prompt=system_prompt)
        subject = res.get("subject", validated.subject)
        body = res.get("body", "No body generated")
        recipient = res.get("recipient", validated.recipient)

        draft_data = {
            "recipient": recipient,
            "subject": subject,
            "body": body
        }
        return ToolResult(
            ok=True,
            data=draft_data,
            summary=f"Drafted email to {recipient} with subject '{subject}'"
        )
