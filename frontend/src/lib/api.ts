import { Task, ToolDefinition, User } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Required for httpOnly cookie authentication & SSE
  });

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    const message = errorData.detail || errorData.message || `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, errorData);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  auth: {
    signup: (data: { email: string; password: string }) =>
      apiRequest<User>("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      apiRequest<{ access_token: string; token_type: string; user: User }>(
        "/api/auth/login",
        {
          method: "POST",
          body: JSON.stringify(data),
        }
      ),
    logout: () =>
      apiRequest<{ message: string }>("/api/auth/logout", {
        method: "POST",
      }),
    me: () => apiRequest<User>("/api/auth/me"),
  },

  tasks: {
    create: (goal: string) =>
      apiRequest<Task>("/api/tasks", {
        method: "POST",
        body: JSON.stringify({ goal }),
      }),
    list: () => apiRequest<Task[]>("/api/tasks"),
    get: (id: string) => apiRequest<Task>(`/api/tasks/${id}`),
    cancel: (id: string) =>
      apiRequest<{ message: string }>(`/api/tasks/${id}/cancel`, {
        method: "POST",
      }),
    approve: (id: string) =>
      apiRequest<{ message: string; success: boolean }>(
        `/api/tasks/${id}/approve`,
        { method: "POST" }
      ),
    reject: (id: string) =>
      apiRequest<{ message: string; success: boolean }>(
        `/api/tasks/${id}/reject`,
        { method: "POST" }
      ),
    retry: (id: string) =>
      apiRequest<{ message: string }>(`/api/tasks/${id}/retry`, {
        method: "POST",
      }),
    getEventsUrl: (id: string) => `${API_BASE_URL}/api/tasks/${id}/events`,
  },

  tools: {
    list: () => apiRequest<ToolDefinition[]>("/api/tools"),
  },

  health: {
    check: () =>
      apiRequest<{
        status: string;
        app: string;
        version: string;
        mock_mode: boolean;
        search_provider: string;
        openai_model: string;
      }>("/api/health"),
  },
};
