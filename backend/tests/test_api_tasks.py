import uuid
import pytest
from httpx import AsyncClient
from app.models import Task, Approval, TaskEvent

@pytest.mark.asyncio
async def test_tasks_api_crud_and_isolation(client: AsyncClient):
    # 1. Sign up User A
    res_a = await client.post("/api/auth/signup", json={"email": "user_a@example.com", "password": "password123"})
    assert res_a.status_code == 200

    # 2. User A creates a task
    create_res = await client.post("/api/tasks", json={"goal": "Compare top AI hackathons"})
    assert create_res.status_code == 200
    task_data = create_res.json()
    task_id = task_data["id"]
    assert task_data["goal"] == "Compare top AI hackathons"

    # 3. User A can list and get the task
    list_res = await client.get("/api/tasks")
    assert list_res.status_code == 200
    assert any(t["id"] == task_id for t in list_res.json())

    get_res = await client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 4. Sign up User B
    client.cookies.clear()
    res_b = await client.post("/api/auth/signup", json={"email": "user_b@example.com", "password": "password123"})
    assert res_b.status_code == 200

    # User B list should NOT contain User A's task
    list_b_res = await client.get("/api/tasks")
    assert list_b_res.status_code == 200
    assert not any(t["id"] == task_id for t in list_b_res.json())

    # User B attempting to get User A's task must get 404
    forbidden_res = await client.get(f"/api/tasks/{task_id}")
    assert forbidden_res.status_code == 404

@pytest.mark.asyncio
async def test_tasks_sse_events_replay(client: AsyncClient):
    # Sign up and create task
    await client.post("/api/auth/signup", json={"email": "sse_user@example.com", "password": "password123"})
    create_res = await client.post("/api/tasks", json={"goal": "SSE streaming test task"})
    task_id = create_res.json()["id"]

    # Request SSE event stream
    sse_res = await client.get(f"/api/tasks/{task_id}/events")
    assert sse_res.status_code == 200
    assert "text/event-stream" in sse_res.headers.get("content-type", "")
    assert sse_res.headers.get("cache-control") == "no-cache"

@pytest.mark.asyncio
async def test_tools_discovery_api(client: AsyncClient):
    res = await client.get("/api/tools")
    assert res.status_code == 200
    tools = res.json()
    assert len(tools) >= 7
    tool_names = [t["name"] for t in tools]
    assert "web_search" in tool_names
    assert "email_send" in tool_names
    assert "calculator" in tool_names
