# TaskPilot AI

> **Autonomous agent for everyday digital work.** State a goal in natural language; TaskPilot understands, dynamically plans a directed acyclic graph (DAG), executes real tools, verifies every output, and pauses for human approval before high-risk operations.

[![Backend Tests](https://img.shields.io/badge/pytest-31%20passed-success)](backend/tests)
[![Frontend Tests](https://img.shields.io/badge/vitest-5%20passed-success)](frontend/src/test)
[![TypeScript](https://img.shields.io/badge/typescript-strict%200%20errors-blue)](frontend)
[![Aesthetic](https://img.shields.io/badge/theme-Ink%20%26%20Brass-amber)](frontend/src/app/globals.css)

---

## 1. Problem Statement
Chatbots answer questions, but knowledge workers spend hours performing multi-step digital chores:
- Gathering facts across fragmented web sources and evaluating credibility.
- Synthesizing unstructured data into clean comparison tables and quantitative summaries.
- Drafting mission communications and dispatching emails.
- Manually double-checking calculations and formatting reports.

Traditional AI chatbots generate hallucinations without verifying facts or running actual tools. Fragile script automations break whenever an API responds with unexpected shapes or errors.

---

## 2. Solution: An Agentic Workflow Engine
**TaskPilot AI is not a chatbot.** It is an autonomous workflow engine designed for digital mission execution:
1. **Dynamic Planning**: Decomposes natural language objectives into an optimal DAG of tool steps, resolving dependencies and input hints.
2. **Observable Execution**: Emits fine-grained Server-Sent Events (SSE) directly to an "Ink & Brass" observatory dashboard in real-time.
3. **Resilient Retry Loop**: Automatically retries failed tool steps with exponential backoff up to 3 attempts.
4. **Human-in-the-Loop Safeguards**: High-risk actions (`email_send`) strictly pause execution with status `WAITING_APPROVAL`, awaiting explicit human confirmation.
5. **Two-Stage Verification**: Rigorously validates tool outputs using deterministic rule checks and LLM consistency verification before declaring success.

---

## 3. Key Features
- **Dynamic DAG Planner**: Generates structured step execution plans on the fly with cycle detection and repair-retry loops.
- **7 Built-in Tools**:
  - `web_search`: Live search provider (Tavily or deterministic Mock) with grounded sources.
  - `web_extract`: SSRF-protected web fetcher extracting sanitized readable content.
  - `calculator`: Safe AST whitelist evaluation (no `eval` or `exec`) with summary statistics.
  - `summarize`: LLM synthesis and executive brief generation.
  - `structured_extract`: JSON / tabular schema extractor with fallback parsing.
  - `email_draft`: Contextual email composer (MEDIUM risk).
  - `email_send`: High-risk delivery engine (HIGH risk, human gatekeeper, simulated dispatch notice or SMTP).
- **Ink & Brass Design System**: Dark slate surfaces (`#0B0D10`), warm ivory typography (`#ECE6DA`), brass accents (`#C8A15A`), Fraunces serif headings, and JetBrains Mono code traces.
- **Real-Time SSE Streaming**: Live step progress, ticking instrument animation, tool telemetry, and agent activity stream.
- **Auditable Agent Trace**: Transparent inspection of goal, DAG plan, input/output data, verification checks, and source citations.
- **Multi-Tenant Cookie Auth**: Secure Argon2-cffi password hashing and HttpOnly JWT cookies.

---

## 4. Architecture & Workflow Engine

### System Architecture
```mermaid
graph TB
    subgraph Frontend ["Frontend (Next.js 14 App Router)"]
        UI["Ink & Brass UI (/app)"]
        SSE_Client["SSE EventSource Client"]
        Auth_Client["Cookie Auth Session"]
    end

    subgraph Backend ["Backend (FastAPI + Async Python)"]
        API["FastAPI Endpoints (/api)"]
        Auth["Security (Argon2 + JWT)"]
        EventBus["Async In-Memory EventBus"]
        Planner["Dynamic DAG Planner"]
        Orchestrator["Async Orchestrator State Machine"]
        Verifier["Two-Stage Verifier"]
        
        subgraph Tools ["Tool Registry"]
            T1["web_search"]
            T2["web_extract (SSRF Safe)"]
            T3["calculator (AST)"]
            T4["summarize"]
            T5["structured_extract"]
            T6["email_draft (Medium)"]
            T7["email_send (High Risk)"]
        end
    end

    subgraph Storage ["Database & External Services"]
        PG[(PostgreSQL 16 / SQLite)]
        OpenAI["OpenAI API / MockLLM"]
        Tavily["Tavily Search / MockSearch"]
    end

    UI --> API
    SSE_Client <--> EventBus
    API --> Orchestrator
    Orchestrator --> Planner
    Planner --> OpenAI
    Orchestrator --> Tools
    Tools --> Tavily
    Orchestrator --> Verifier
    Verifier --> OpenAI
    Orchestrator --> PG
    API --> PG
```

### Execution Lifecycle
```mermaid
sequenceDiagram
    autonumber
    actor User as Knowledge Worker
    participant Front as Frontend (/app)
    participant Orch as Orchestrator
    participant Plan as Planner
    participant Tool as Tool Registry
    participant Verif as Verifier

    User->>Front: Submit Goal Prompt
    Front->>Orch: POST /api/tasks
    Orch->>Plan: Generate DAG Plan
    Plan-->>Orch: Validated Plan JSON
    Orch-->>Front: SSE: PLAN_CREATED
    
    loop For Each Step in DAG
        Orch-->>Front: SSE: STEP_STARTED
        alt High Risk Step (e.g. email_send)
            Orch->>Orch: Status = WAITING_APPROVAL
            Orch-->>Front: SSE: APPROVAL_REQUIRED
            User->>Front: Click [Approve]
            Front->>Orch: POST /api/tasks/{id}/approve
            Orch-->>Front: SSE: APPROVAL_RESOLVED
        end
        Orch->>Tool: Execute Tool (up to 3 retries)
        Tool-->>Orch: ToolResult {ok, data, sources}
        Orch-->>Front: SSE: STEP_COMPLETED
    end

    Orch->>Verif: Run Rule Checks & LLM Consistency
    Verif-->>Orch: Verification Report {passed: true}
    Orch-->>Front: SSE: TASK_COMPLETED
    Front->>User: Display Interactive Report & Sources
```

---

## 5. Technology Stack
- **Backend**:
  - Python 3.10+
  - FastAPI & Uvicorn
  - Pydantic v2 & `pydantic-settings`
  - SQLAlchemy 2.0 Async (`postgresql+asyncpg://` for production, `sqlite+aiosqlite://` for tests)
  - Alembic (async migration environment)
  - Argon2-cffi & PyJWT (secure auth)
  - HTTPX, BeautifulSoup4, OpenAI official SDK
  - Pytest & Pytest-asyncio
- **Frontend**:
  - Next.js 14.2 (App Router) & TypeScript Strict
  - Tailwind CSS 3.4 (Custom Ink & Brass theme)
  - Framer Motion (restrained micro-animations)
  - Lucide React (editorial iconography)
  - TanStack React Query & Sonner
  - React Markdown & Remark GFM
  - Recharts (responsive metrics charts)
  - Vitest & Testing Library React
- **Database & Storage**:
  - PostgreSQL 16 (via Docker Compose)

---

## 6. Repository Structure
```
TaskPilot-AI/
├── backend/
│   ├── alembic/                 # Async Alembic database migrations
│   ├── app/
│   │   ├── api/                 # FastAPI routes (auth, tasks, tools, health)
│   │   ├── core/                # Config, security (Argon2), error handlers
│   │   ├── database/            # Async SQLAlchemy engine & base
│   │   ├── models/              # User, Task, TaskStep, ToolExecution, Approval, Event
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/            # LLM & Search providers (OpenAI, Tavily, Mocks), EventBus
│   │   └── agents/
│   │       ├── planner/         # Dynamic DAG generation with retry-repair
│   │       ├── orchestrator/    # Async background task execution & state machine
│   │       ├── tools/           # 7 Sandboxed tools with SSRF & AST safety
│   │       └── verification/    # Two-stage rule + LLM consistency verifier
│   ├── scripts/                 # E2E test scripts & terminal verifications
│   ├── tests/                   # 31 Pytest async unit & integration tests
│   ├── alembic.ini              # Alembic configuration
│   ├── pytest.ini               # Pytest async configuration
│   └── requirements.txt         # Frozen exact backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 14 App Router pages
│   │   │   ├── page.tsx         # Editorial landing page (10 sections)
│   │   │   ├── login/           # Auth login & instant demo login
│   │   │   ├── signup/          # User registration
│   │   │   ├── app/             # Protected dashboard & mission controller
│   │   │   │   ├── page.tsx     # Command center & suggestion chips
│   │   │   │   ├── tasks/       # Mission history & live execution page
│   │   │   │   ├── tools/       # Tool capability matrix & JSON schema viewer
│   │   │   │   └── settings/    # Model settings & theme customizer
│   │   ├── components/          # Reusable Ink & Brass UI components
│   │   ├── lib/                 # API client with credentials & auth context
│   │   └── test/                # Vitest frontend component tests
│   ├── tailwind.config.ts       # Ink & Brass design token configuration
│   ├── tsconfig.json            # Strict TypeScript configuration
│   └── package.json             # Pinned frontend dependencies
├── docker-compose.yml           # Local PostgreSQL 16 service
├── .env.example                 # Environment configuration template
└── README.md                    # Project documentation
```

---

## 7. Prerequisites & Environment Setup
- **Python**: 3.10, 3.11, or 3.12
- **Node.js**: 18.17+ or 20.x
- **Docker**: Docker Desktop (for local PostgreSQL 16)

### Clone & Configure Environment
```bash
git clone https://github.com/your-username/TaskPilot-AI.git
cd TaskPilot-AI
cp .env.example .env
```

---

## 8. Environment Variables Reference
| Variable | Default | Description |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | *(empty in mock)* | OpenAI API key for planner, LLM tools, and verifier |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model selection |
| `DATABASE_URL` | `postgresql+asyncpg://taskpilot:taskpilot_secret_password@localhost:5432/taskpilot` | Async PostgreSQL database connection URL |
| `SEARCH_API_KEY` | *(empty in mock)* | Tavily Search API key |
| `SEARCH_PROVIDER` | `tavily` | Search engine provider (`tavily` or `mock`) |
| `SECRET_KEY` | *(32+ chars)* | Secret key for JWT signing |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Allowed CORS origin for credentials |
| `MOCK_MODE` | `true` | When `true`, activates deterministic Mock providers without external keys |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend browser fetch calls |

---

## 9. Running Locally

### Step 1: Start PostgreSQL Database
```bash
docker compose up -d db
```

### Step 2: Set Up & Start Backend
```bash
cd backend
python -m venv .venv

# Windows Powershell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend will be running at [http://127.0.0.1:8000](http://127.0.0.1:8000) (OpenAPI docs at `/docs`).*

### Step 3: Set Up & Start Frontend
```bash
cd ../frontend
npm install
npm run dev -- -p 3000
```
*Frontend will be running at [http://localhost:3000](http://localhost:3000).*

---

## 10. Demo Workflow & Example Prompts

Visit `http://localhost:3000/login` and click **"Use Instant Demo Account"** to sign in immediately without manual registration.

### Default Hackathon Demo Prompt:
> *"Research the top AI hackathons currently accepting applications, compare their deadlines, prizes and requirements, and create a concise report."*
- **What happens:** TaskPilot plans a DAG (`web_search` -> `structured_extract` -> `summarize`), fetches mock/live hackathon data, generates a comparison table, and verifies all sources.

### 4 Additional Curated Prompts:
1. **Analyze Data & Compute Statistics:**
   > *"Calculate the mean, median, and compound annual growth rate for monthly active users: [12000, 14500, 19200, 26000, 35400, 48000]. Compare the growth trajectory and summarize findings."*
2. **Human Approval & Email Dispatch:**
   > *"Draft an executive notification email to team@example.com summarizing our upcoming AI hackathon strategy and dispatch the communication."*
   > *(Triggers high-risk approval modal for `email_send` with [Approve] / [Reject] actions).*
3. **Competitive Technical Analysis:**
   > *"Extract and compare the pricing models, context window limits, and latency profiles of GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro into a structured comparison table."*
4. **Research & Executive Synthesis:**
   > *"Perform a market intelligence scan on autonomous agentic workflow frameworks in 2026, identify key architectural patterns, and generate a brief."*

---

## 11. Screenshots & UI Walkthrough
- **Landing Page (`/`)**: Ink & Brass aesthetic with Fraunces serif typography, 10 complete sections, and live workflow diagram.
- **Mission Controller (`/app`)**: Large command box with Ctrl/Cmd+Enter keyboard shortcut, suggestion chips, and recent mission cards.
- **Execution Page (`/app/tasks/[id]`)**:
  - Ticking instrument radar sweep animation for active steps.
  - Live SSE agent activity stream.
  - Transparent Agent Trace tab displaying step reasoning and inputs/outputs.
  - Interactive Result tab with Markdown rendering, comparison tables, metrics cards, Recharts charts, and grounded source links.
  - Human Approval Modal with risk badges and full action payload inspection.
- **Tool Catalog (`/app/tools`)**: Real-time capability matrix displaying risk levels and Pydantic input schemas.
- **Theme & Settings (`/app/settings`)**: Theme switcher (Ink Dark vs. Editorial Light) and provider telemetry.

---

## 12. API Documentation & Endpoints

TaskPilot includes interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### Key Endpoints:
| Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/login` | Authenticate user and receive HttpOnly cookie |
| `POST` | `/api/auth/logout` | Clear session cookie |
| `GET` | `/api/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/tasks` | Create and launch an autonomous mission |
| `GET` | `/api/tasks` | List user missions with status and timestamps |
| `GET` | `/api/tasks/{id}` | Hydrate full mission state, steps, results, and trace |
| `POST` | `/api/tasks/{id}/approve` | Approve a paused high-risk action (`WAITING_APPROVAL`) |
| `POST` | `/api/tasks/{id}/reject` | Reject a paused high-risk action |
| `POST` | `/api/tasks/{id}/cancel` | Abort a running mission |
| `POST` | `/api/tasks/{id}/retry` | Retry a failed mission |
| `GET` | `/api/tasks/{id}/events` | SSE stream for real-time event streaming with replay |
| `GET` | `/api/tools` | Discover available tools, descriptions, and schemas |
| `GET` | `/api/health` | Health check endpoint |

---

## 13. Security & Safety Mechanisms
- **Input Validation**: All tool parameters are validated using Pydantic v2 schemas before execution.
- **SSRF Protection**: `web_extract` performs DNS resolution before requests and strictly blocks private (RFC 1918), loopback (`127.0.0.1`), link-local (`169.254.0.0/16`), and AWS metadata endpoints.
- **Safe Calculator**: The arithmetic engine parses code into an Abstract Syntax Tree (AST) allowlist (`ast.BinOp`, `ast.UnaryOp`, `ast.Call` for whitelisted math functions). `eval()`, `exec()`, imports, and builtins are strictly prohibited.
- **High-Risk Human Gatekeeper**: The backend enforces that tools with `risk_level: HIGH` (`email_send`) cannot execute automatically. The orchestrator transitions to `WAITING_APPROVAL` and waits for an explicit approval API call.
- **Authentication Security**: Passwords hashed using Argon2-cffi. JWTs are stored in HttpOnly, SameSite=Lax (or None in production cross-origin) cookies.
- **Ownership Isolation**: All task queries verify `task.user_id == current_user.id`.

---

## 14. Verification & Testing Strategy

### Backend Tests (Pytest)
The backend test suite runs 31 automated tests on an isolated async SQLite database with dependency-injected mocks:
```bash
cd backend
.\.venv\Scripts\pytest -v
```
**Test Results:** `31 passed, 1 warning in 10.70s`
- `test_auth.py`: Password hashing, signup, duplicate email, login, protected routes (5 tests).
- `test_planner.py`: DAG validation, cyclic dependency rejection, unknown tool rejection, repair-retry loops (5 tests).
- `test_orchestrator.py`: End-to-end execution, retry loops, retry exhaustion, high-risk approval pause/resume, task cancellation (5 tests).
- `test_tools.py`: Tool registry, web search, SSRF socket-level protection, AST calculator safety, summarize, structured extract, email draft, email send (8 tests).
- `test_verifier.py`: Rule checks (empty output, web sources, malformed URLs) and LLM verification (4 tests).
- `test_api_tasks.py`: CRUD isolation, SSE event replay, tool discovery (3 tests).

### Frontend Tests (Vitest)
```bash
cd frontend
npm test
```
**Test Results:** `5 passed in 2.75s`
- Command box input & keyboard shortcut execution.
- Suggestion chips auto-filling prompts.
- Live step timeline status indicators (pending, active, completed, failed).
- Approval dialog modal rendering and action dispatch.

### Automated End-to-End Client Test
```bash
cd backend
python scripts/verify_full_system.py
```
Validates all 7 frontend HTML routes, user registration, JWT cookies, SSE streaming parsing (17 events), high-risk approval lifecycle, and tool catalog.

---

## 15. Production Deployment Guide

### Option A: Render / Railway (Backend + Managed Postgres)
1. **Database**: Create a Managed PostgreSQL 16 instance. Copy the connection string.
2. **Backend Web Service**:
   - Environment: Python 3.11+
   - Build Command: `pip install -r requirements.txt && alembic upgrade head`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     - `DATABASE_URL`: `postgresql+asyncpg://user:pass@host:port/dbname`
     - `FRONTEND_ORIGIN`: `https://your-frontend.vercel.app`
     - `SECRET_KEY`: `<generate-random-32-chars>`
     - `OPENAI_API_KEY`: `<your-openai-key>`
     - `SEARCH_API_KEY`: `<your-tavily-key>`
     - `MOCK_MODE`: `false`

### Option B: Vercel (Frontend)
1. Connect repository to Vercel and set root directory to `frontend`.
2. Configure Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com`
3. Cross-Site Cookie Configuration:
   - When frontend and backend are hosted on separate domains, set `SameSite=None` and `Secure=True` in `backend/app/api/routes/auth.py`.

---

## 16. Roadmap
- [ ] **Multi-Agent Orchestration**: Specialized sub-agents collaborating on long-running research tracks.
- [ ] **Custom Tool Builder**: Allow users to define OpenAPI-based tools directly in the UI.
- [ ] **Webhook Integrations**: Slack and Discord notifications when missions require approval or finish.
- [ ] **Vector Memory**: Long-term semantic recall across past task executions.

---

## 17. Contributors & License
Built with passion for autonomous workflow engineering. Distributed under the MIT License.
