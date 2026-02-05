import { API_BASE } from "../config/endpoints";
import { getToken } from "./keycloak";

export async function apiRequest(path: string, options: RequestInit = {}) {
  const token = await getToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  return res.json();
}

export async function apiGet(path: string) {
  return apiRequest(path);
}

export async function apiPost(path: string, body: unknown) {
  return apiRequest(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
