import { API_BASE } from "../config/endpoints";
import { getToken } from "./keycloak";

export async function apiGet(path: string) {
  const token = await getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return res.json();
}
