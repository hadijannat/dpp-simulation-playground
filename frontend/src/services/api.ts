import { API_BASE } from "../config/endpoints";
import { getToken } from "./keycloak";
import { getSelectedRole } from "../stores/roleStore";

export class ApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function parseResponse(res: Response) {
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return res.json();
  }
  const text = await res.text();
  return text ? { message: text } : null;
}

export async function apiRequest<T = unknown>(path: string, options: RequestInit = {}) {
  const token = await getToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  } else {
    headers.set("X-Dev-User", "demo-user");
    headers.set("X-Dev-Roles", getSelectedRole());
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const payload = await parseResponse(res);
  if (!res.ok) {
    const message = (payload as { detail?: string })?.detail ?? res.statusText;
    throw new ApiError(message || "Request failed", res.status, payload);
  }
  return payload as T;
}

export async function apiGet<T = unknown>(path: string) {
  return apiRequest<T>(path);
}

export async function apiPost<T = unknown>(path: string, body: unknown) {
  return apiRequest<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
