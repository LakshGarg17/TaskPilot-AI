from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mock_mode": settings.MOCK_MODE,
        "search_provider": settings.SEARCH_PROVIDER,
        "openai_model": settings.OPENAI_MODEL
    }
