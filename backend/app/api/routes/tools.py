from fastapi import APIRouter
from app.agents.tools.registry import tool_registry
import app.agents.tools  # Ensure tools loaded

router = APIRouter(prefix="/tools", tags=["Tools"])

@router.get("")
async def list_available_tools():
    return tool_registry.get_descriptions()
