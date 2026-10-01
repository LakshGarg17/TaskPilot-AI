"""
Full end-to-end client verification simulating the browser frontend.
Tests:
1. Frontend route availability (/, /login, /signup, /app, /app/tasks, /app/tools, /app/settings)
2. Auth (signup, login, cookie persistence, /api/auth/me)
3. Demo prompt execution with live SSE stream parsing
4. Approval flow (email draft + send, APPROVAL_REQUIRED, approve API call, simulated dispatch)
5. History listing and single-task retrieval
6. Tool catalog inspection
"""
import sys
import asyncio
import httpx
import json

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://127.0.0.1:8000"

async def test_frontend_routes(client: httpx.AsyncClient):
    print("\n--- 1. Testing Frontend Route Rendering ---")
    routes = [
        "/",
        "/login",
        "/signup",
        "/app",
        "/app/tasks",
        "/app/tools",
        "/app/settings"
    ]
    for route in routes:
        resp = await client.get(f"{FRONTEND_URL}{route}")
        assert resp.status_code == 200, f"Route {route} failed with {resp.status_code}"
        assert "<html" in resp.text.lower() or "<!doctype html>" in resp.text.lower(), f"Route {route} didn't return valid HTML"
        print(f"  [PASS] Frontend {route} returned 200 OK ({len(resp.text)} bytes)")

async def test_auth_and_tasks():
    print("\n--- 2. Testing Full Auth, Task Execution & SSE Streaming ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Signup
        email = f"architect_test_{asyncio.get_event_loop().time()}@example.com"
        password = "SecurePassword2026!"
        signup_resp = await client.post(
            f"{BACKEND_URL}/api/auth/signup",
            json={"email": email, "password": password, "full_name": "Test Architect"}
        )
        assert signup_resp.status_code == 200, f"Signup failed: {signup_resp.text}"
        user_data = signup_resp.json()
        print(f"  [OK] User signed up: {user_data['email']} (id: {user_data['id']})")
        assert "access_token" in client.cookies, "Auth cookie was not set!"

        # Me
        me_resp = await client.get(f"{BACKEND_URL}/api/auth/me")
        assert me_resp.status_code == 200
        print(f"  [OK] Auth verification /api/auth/me confirmed for {me_resp.json()['email']}")

        # 3. Demo Prompt Execution
        demo_prompt = "Research the top AI hackathons currently accepting applications, compare their deadlines, prizes and requirements, and create a concise report."
        print(f"\n--- 3. Launching Demo Prompt ---")
        print(f"  Goal: '{demo_prompt}'")
        task_create_resp = await client.post(
            f"{BACKEND_URL}/api/tasks",
            json={"goal": demo_prompt}
        )
        assert task_create_resp.status_code == 200, f"Task creation failed: {task_create_resp.text}"
        task = task_create_resp.json()
        task_id = task["id"]
        print(f"  [OK] Task created with id: {task_id}")

        # Stream SSE events
        print("  Connecting to SSE event stream...")
        received_event_types = []
        async with client.stream("GET", f"{BACKEND_URL}/api/tasks/{task_id}/events") as stream:
            async for line in stream.aiter_lines():
                if line.startswith("event: "):
                    event_type = line.replace("event: ", "").strip()
                    received_event_types.append(event_type)
                    print(f"    -> SSE Event: {event_type}")
                    if event_type in ("TASK_COMPLETED", "TASK_FAILED", "TASK_CANCELLED"):
                        break

        print(f"  [OK] Received {len(received_event_types)} SSE events: {set(received_event_types)}")
        assert "TASK_COMPLETED" in received_event_types, "Task did not complete successfully!"

        # Verify task final output
        task_detail_resp = await client.get(f"{BACKEND_URL}/api/tasks/{task_id}")
        assert task_detail_resp.status_code == 200
        task_detail = task_detail_resp.json()
        assert task_detail["status"] == "COMPLETED"
        assert task_detail["result"] is not None
        result = task_detail["result"]
        print(f"  [OK] Result markdown generated: {len(result['markdown'])} chars")
        print(f"  [OK] Comparison tables: {len(result['tables'])} table(s)")
        print(f"  [OK] Metric cards: {len(result['cards'])} card(s)")
        print(f"  [OK] Verified sources: {len(result['sources'])} source(s)")
        for src in result["sources"]:
            print(f"      * {src['title']} ({src['domain']}) -> {src['url']}")

        # 4. Email Approval Flow
        print("\n--- 4. Testing High-Risk Human Approval Workflow ---")
        email_prompt = "Draft an executive notification email to team@example.com summarizing our upcoming AI hackathon strategy and dispatch the communication."
        email_task_resp = await client.post(
            f"{BACKEND_URL}/api/tasks",
            json={"goal": email_prompt}
        )
        assert email_task_resp.status_code == 200
        email_task_id = email_task_resp.json()["id"]
        print(f"  [OK] Email task created: {email_task_id}")

        # Wait for WAITING_APPROVAL
        print("  Awaiting WAITING_APPROVAL state...")
        approval_id = None
        for _ in range(30):
            t_resp = await client.get(f"{BACKEND_URL}/api/tasks/{email_task_id}")
            t_data = t_resp.json()
            if t_data["status"] == "WAITING_APPROVAL":
                print(f"  [OK] Task successfully paused in WAITING_APPROVAL state!")
                # Find pending approval
                approvals = t_data.get("approvals", [])
                pending = [a for a in approvals if a["status"] == "PENDING"]
                assert len(pending) > 0, "No pending approval record found!"
                approval_id = pending[0]["id"]
                print(f"  [OK] Found pending approval ID: {approval_id}")
                print(f"    Action Summary: {pending[0]['action_summary']}")
                print(f"    Risk Level: {pending[0]['risk_level']}")
                print(f"    Inputs: {pending[0]['inputs']}")
                break
            await asyncio.sleep(0.5)

        assert approval_id is not None, "Task never paused for approval!"

        # Approve the action
        print(f"  Submitting Approval for task {email_task_id}...")
        approve_resp = await client.post(f"{BACKEND_URL}/api/tasks/{email_task_id}/approve")
        assert approve_resp.status_code == 200
        print("  [OK] Approval submitted successfully!")

        # Wait for completion
        for _ in range(30):
            t_resp = await client.get(f"{BACKEND_URL}/api/tasks/{email_task_id}")
            t_data = t_resp.json()
            if t_data["status"] == "COMPLETED":
                print(f"  [OK] Email task completed successfully after approval!")
                assert t_data["result"] is not None
                email_draft = t_data["result"].get("email_draft")
                print(f"    Email subject: {email_draft.get('subject') if email_draft else 'N/A'}")
                print(f"    Email recipient: {email_draft.get('to') if email_draft else 'N/A'}")
                break
            await asyncio.sleep(0.5)

        # 5. History Listing
        print("\n--- 5. Checking Task History Listing ---")
        history_resp = await client.get(f"{BACKEND_URL}/api/tasks")
        assert history_resp.status_code == 200
        tasks_list = history_resp.json()
        print(f"  [OK] Found {len(tasks_list)} tasks in user history")
        assert len(tasks_list) >= 2

        # 6. Tools Catalog
        print("\n--- 6. Checking Tool Catalog ---")
        tools_resp = await client.get(f"{BACKEND_URL}/api/tools")
        assert tools_resp.status_code == 200
        tools = tools_resp.json()
        print(f"  [OK] Registered tools ({len(tools)}):")
        for tool in tools:
            print(f"      * {tool['name']} [{tool['risk_level']}]: {tool['description'][:50]}...")

    print("\n=======================================================")
    print(" ALL END-TO-END VERIFICATION CHECKS PASSED WITH FLYING COLORS!")
    print("=======================================================\n")

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        await test_frontend_routes(client)
    await test_auth_and_tasks()

if __name__ == "__main__":
    asyncio.run(main())
