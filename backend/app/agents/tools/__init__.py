from app.agents.tools.registry import tool_registry
from app.agents.tools.web_search import WebSearchTool
from app.agents.tools.web_extract import WebExtractTool
from app.agents.tools.calculator import CalculatorTool
from app.agents.tools.summarize import SummarizeTool
from app.agents.tools.structured_extract import StructuredExtractTool
from app.agents.tools.email_draft import EmailDraftTool
from app.agents.tools.email_send import EmailSendTool

# Register all default tools
tool_registry.register(WebSearchTool())
tool_registry.register(WebExtractTool())
tool_registry.register(CalculatorTool())
tool_registry.register(SummarizeTool())
tool_registry.register(StructuredExtractTool())
tool_registry.register(EmailDraftTool())
tool_registry.register(EmailSendTool())
