import asyncio
import json
import sys
import os
from httpx import AsyncClient, ASGITransport
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))
from app.main import app

async def run_demo():
    print("=" * 60)
    print("RUNNING DEMO PROMPT END-TO-END (MOCK_MODE=True)")
    print("=" * 60)

    demo_prompt = "Research the top AI hackathons currently accepting applications, compare their deadlines, prizes and requirements, and create a concise report."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as client:
        # 1. Sign up user
        email = f"demo_runner_{int(asyncio.get_event_loop().time())}@example.com"
        res_signup = await client.post("/api/auth/signup", json={"email": email, "password": "DemoPassword123!"})
        print(f"[AUTH] Created user {email} (status: {res_signup.status_code})")

        # 2. Launch task with Demo Prompt
        res_task = await client.post("/api/tasks", json={"goal": demo_prompt})
        task_data = res_task.json()
        task_id = task_data["id"]
        print(f"[TASK LAUNCHED] Task ID: {task_id}")
        print(f"[GOAL] {demo_prompt}\n")

        # 3. Poll until completed (waiting for background orchestrator)
        for i in range(20):
            await asyncio.sleep(0.5)
            res = await client.get(f"/api/tasks/{task_id}")
            current = res.json()
            status = current.get("status")
            steps_done = len([s for s in current.get("steps", []) if s["status"] == "COMPLETED"])
            total_steps = len(current.get("steps", []))
            print(f"  [STATUS POLL] Status: {status} | Steps completed: {steps_done}/{total_steps}")
            if status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"):
                break

        # 4. Display final plan, events, and sources
        final_res = await client.get(f"/api/tasks/{task_id}")
        task_final = final_res.json()

        print("\n" + "=" * 60)
        print("RESULTING PLAN:")
        print(json.dumps(task_final.get("plan"), indent=2))

        print("\n" + "=" * 60)
        print("EXECUTED STEPS:")
        for s in task_final.get("steps", []):
            print(f"  - Step {s['step_key']}: {s['description']} (Tool: {s['tool_name']}, Status: {s['status']})")

        print("\n" + "=" * 60)
        print("SOURCES GROUNDED:")
        sources = task_final.get("result", {}).get("sources", [])
        for src in sources:
            print(f"  - [{src.get('domain')}] {src.get('title')}: {src.get('url')}")

        print("\n" + "=" * 60)
        print("FINAL VERIFIED REPORT PREVIEW (First 400 chars):")
        md = task_final.get("result", {}).get("markdown", "")
        print(md[:400] + "...")
        print("=" * 60)
        print(f"DEMO E2E RUN FINISHED: Status={task_final.get('status')}")

if __name__ == "__main__":
    asyncio.run(run_demo())
