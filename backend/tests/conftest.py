import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.database.base import Base
import app.models  # ensure models registered
from app.database.session import get_db
from app.main import app

# Shared SQLite async engine for tests
import os

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testmemdb?mode=memory&cache=shared&uri=true"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

from app.core.config import settings
settings.MOCK_MODE = True

import app.agents.orchestrator.orchestrator as orch_module
import app.api.routes.tasks as tasks_module

@pytest_asyncio.fixture(autouse=True)
def patch_session_local(monkeypatch):
    monkeypatch.setattr(orch_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(tasks_module, "AsyncSessionLocal", TestingSessionLocal)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
