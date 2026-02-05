import { apiRequest, ApiError } from "../api";

/* ------------------------------------------------------------------ */
/*  Mocks                                                             */
/* ------------------------------------------------------------------ */

// Mock getToken from keycloak service
vi.mock("../keycloak", () => ({
  getToken: vi.fn(),
}));

// Mock getSelectedRole from roleStore
vi.mock("../../stores/roleStore", () => ({
  getSelectedRole: () => "manufacturer",
}));

// Mock the API_BASE endpoint
vi.mock("../../config/endpoints", () => ({
  API_BASE: "http://localhost:8000",
}));

// Import after mocks are declared so they take effect
import { getToken } from "../keycloak";

const mockGetToken = vi.mocked(getToken);

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function mockFetch(response: {
  ok: boolean;
  status: number;
  statusText?: string;
  json?: unknown;
  text?: string;
  contentType?: string;
}) {
  const headers = new Headers();
  if (response.contentType) {
    headers.set("content-type", response.contentType);
  } else if (response.json !== undefined) {
    headers.set("content-type", "application/json");
  }

  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: response.ok,
    status: response.status,
    statusText: response.statusText || "Error",
    headers,
    json: () => Promise.resolve(response.json),
    text: () => Promise.resolve(response.text || ""),
  } as unknown as Response);
}

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("apiRequest", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sets Authorization header when token is available", async () => {
    mockGetToken.mockResolvedValue("my-jwt-token");
    mockFetch({ ok: true, status: 200, json: { data: "ok" } });

    await apiRequest("/test");

    const fetchCall = vi.mocked(globalThis.fetch).mock.calls[0];
    const [url, options] = fetchCall;
    expect(url).toBe("http://localhost:8000/test");

    const headers = options?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer my-jwt-token");
  });

  it("sets X-Dev-User and X-Dev-Roles headers when no token", async () => {
    mockGetToken.mockResolvedValue(null);
    mockFetch({ ok: true, status: 200, json: { data: "ok" } });

    await apiRequest("/test");

    const fetchCall = vi.mocked(globalThis.fetch).mock.calls[0];
    const headers = fetchCall[1]?.headers as Headers;
    expect(headers.get("X-Dev-User")).toBe("demo-user");
    expect(headers.get("X-Dev-Roles")).toBe("manufacturer");
  });

  it("throws ApiError on non-OK response", async () => {
    mockGetToken.mockResolvedValue(null);
    mockFetch({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: { detail: "Resource not found" },
    });

    await expect(apiRequest("/not-found")).rejects.toThrow(ApiError);

    try {
      await apiRequest("/not-found");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(404);
      expect(apiErr.message).toBe("Resource not found");
    }
  });

  it("includes parsed error body payload in the ApiError", async () => {
    mockGetToken.mockResolvedValue(null);
    mockFetch({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: { detail: "Validation failed", errors: [{ field: "name" }] },
    });

    try {
      await apiRequest("/validate");
    } catch (err) {
      const apiErr = err as ApiError;
      expect(apiErr.payload).toEqual({
        detail: "Validation failed",
        errors: [{ field: "name" }],
      });
    }
  });

  it("returns parsed JSON on successful response", async () => {
    mockGetToken.mockResolvedValue("token");
    mockFetch({ ok: true, status: 200, json: { id: "abc", name: "test" } });

    const result = await apiRequest<{ id: string; name: string }>("/resource");
    expect(result).toEqual({ id: "abc", name: "test" });
  });

  it("handles non-JSON text responses", async () => {
    mockGetToken.mockResolvedValue(null);
    mockFetch({
      ok: true,
      status: 200,
      text: "plain text response",
      contentType: "text/plain",
    });

    const result = await apiRequest("/text");
    expect(result).toEqual({ message: "plain text response" });
  });

  it("passes through custom request options", async () => {
    mockGetToken.mockResolvedValue(null);
    mockFetch({ ok: true, status: 201, json: { created: true } });

    await apiRequest("/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "test" }),
    });

    const fetchCall = vi.mocked(globalThis.fetch).mock.calls[0];
    const options = fetchCall[1];
    expect(options?.method).toBe("POST");
    expect(options?.body).toBe('{"name":"test"}');
  });

  it("uses statusText as fallback error message when detail is missing", async () => {
    mockGetToken.mockResolvedValue(null);
    mockFetch({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: {},
    });

    try {
      await apiRequest("/error");
    } catch (err) {
      const apiErr = err as ApiError;
      expect(apiErr.message).toBe("Internal Server Error");
      expect(apiErr.status).toBe(500);
    }
  });
});
