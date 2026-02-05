import { API_BASE } from "../config/endpoints";

export async function apiGet(path: string) {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
}
