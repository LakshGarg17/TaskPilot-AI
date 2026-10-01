from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import TaskPilotError, taskpilot_exception_handler
from app.api.routes import health

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (MOCK_MODE={settings.MOCK_MODE})")
    # Startup tasks: check DB, mark orphaned RUNNING tasks as FAILED
    try:
        from app.agents.orchestrator.orchestrator import cleanup_orphaned_tasks
        await cleanup_orphaned_tasks()
    except Exception as e:
        logger.warning(f"Orphan cleanup error on startup: {e}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register error handlers
    app.add_exception_handler(TaskPilotError, taskpilot_exception_handler)

    # Include routers
    app.include_router(health.router, prefix="/api")
    from app.api.routes import auth, tasks, tools
    app.include_router(auth.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(tools.router, prefix="/api")

    return app

app = create_app()
