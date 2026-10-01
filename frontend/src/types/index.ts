export interface User {
  id: string;
  email: string;
  created_at: string;
}

export type TaskStatus =
  | "PENDING"
  | "PLANNING"
  | "RUNNING"
  | "WAITING_APPROVAL"
  | "VERIFYING"
  | "COMPLETED"
  | "COMPLETED_WITH_WARNINGS"
  | "FAILED"
  | "CANCELLED";

export type StepStatus =
  | "PENDING"
  | "RUNNING"
  | "WAITING_APPROVAL"
  | "COMPLETED"
  | "FAILED"
  | "SKIPPED"
  | "RETRYING";

export interface TaskStep {
  id: string;
  step_number: number;
  step_key: string;
  description: string;
  tool_name: string;
  depends_on: string[];
  input_hints: Record<string, any>;
  expected_output?: string | null;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  status: StepStatus;
  retry_count: number;
  output_data?: Record<string, any> | null;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface ToolExecution {
  id: string;
  step_id?: string | null;
  tool_name: string;
  inputs: Record<string, any>;
  output?: Record<string, any> | null;
  ok: boolean;
  sources: Array<{ title: string; url: string; domain?: string }>;
  duration_ms: number;
  attempt: number;
  created_at: string;
}

export interface SourceItem {
  title: string;
  url: string;
  domain?: string;
}

export interface VerificationCheck {
  name: string;
  passed: boolean;
  detail: string;
}

export interface VerificationReport {
  passed: boolean;
  checks: VerificationCheck[];
}

export interface TaskResult {
  id: string;
  task_id: string;
  markdown: string;
  tables: Array<{
    title: string;
    headers: string[];
    rows: Array<Record<string, any>>;
  }>;
  cards: Array<{
    title: string;
    value: string;
    description?: string;
  }>;
  chart_data?: {
    title: string;
    data: Array<{ name: string; value: number }>;
  } | null;
  sources: SourceItem[];
  email_draft?: {
    recipient: string;
    subject: string;
    body: string;
  } | null;
  verification_report?: VerificationReport | null;
  created_at: string;
}

export interface Approval {
  id: string;
  task_id: string;
  step_id: string;
  user_id: string;
  tool_name: string;
  action_summary: string;
  inputs: Record<string, any>;
  risk_level: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  created_at: string;
  resolved_at?: string | null;
}

export interface TaskEvent {
  id: string;
  task_id: string;
  event_type: string;
  step_id?: string | null;
  tool?: string | null;
  message: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  goal: string;
  status: TaskStatus;
  plan?: {
    goal: string;
    steps: Array<{
      id: string;
      description: string;
      tool: string;
      depends_on: string[];
      input_hints: Record<string, any>;
      expected_output?: string;
      risk_level: string;
    }>;
    verification_requirements: string[];
  } | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  steps: TaskStep[];
  tool_executions: ToolExecution[];
  result?: TaskResult | null;
  approvals: Approval[];
}

export interface ToolDefinition {
  name: string;
  description: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  schema: Record<string, any>;
}
