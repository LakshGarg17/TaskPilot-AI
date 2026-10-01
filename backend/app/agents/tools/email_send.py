import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, EmailStr
from app.agents.tools.base import BaseTool, ToolResult
from app.core.config import settings

class EmailSendInput(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Subject of the email")
    body: str = Field(..., description="Body of the email")

class EmailSendTool(BaseTool):
    name = "email_send"
    description = "Dispatches an email to external recipients. Requires explicit human approval before execution."
    risk_level = "HIGH"
    input_schema = EmailSendInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        validated = self.validate_inputs(inputs)

        # Check if actual SMTP configuration is provided
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
                msg["To"] = validated.to
                msg["Subject"] = validated.subject
                msg.attach(MIMEText(validated.body, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                return ToolResult(
                    ok=True,
                    data={"to": validated.to, "subject": validated.subject, "status": "delivered_via_smtp"},
                    summary=f"Sent email via SMTP to {validated.to}"
                )
            except Exception as e:
                return ToolResult(
                    ok=False,
                    error=f"SMTP dispatch failed: {str(e)}",
                    summary=f"Failed to send email to {validated.to}"
                )

        # Honest simulation when no SMTP is configured
        simulated_msg = "sent (simulated, no SMTP configured)"
        return ToolResult(
            ok=True,
            data={
                "to": validated.to,
                "subject": validated.subject,
                "body_preview": validated.body[:150] + "..." if len(validated.body) > 150 else validated.body,
                "status": simulated_msg
            },
            summary=f"Approved action completed: {simulated_msg} to {validated.to}"
        )
