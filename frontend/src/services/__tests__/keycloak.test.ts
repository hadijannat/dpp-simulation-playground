import { beforeEach, describe, expect, it, vi } from "vitest";

const { mockInstance } = vi.hoisted(() => ({
  mockInstance: {
    init: vi.fn(),
    updateToken: vi.fn(),
    authenticated: false,
    token: null as string | null,
  },
}));

vi.mock("keycloak-js", () => ({
  default: vi.fn(function MockKeycloak() {
    return mockInstance;
  }),
}));

vi.mock("../../config/keycloak", () => ({
  keycloakConfig: {
    url: "http://localhost:8080",
    realm: "test-realm",
    clientId: "test-client",
  },
}));

async function loadKeycloakModule() {
  return import("../keycloak");
}

describe("keycloak service", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    mockInstance.authenticated = false;
    mockInstance.token = null;
  });

  it("initializes only once when called concurrently", async () => {
    mockInstance.init.mockResolvedValue(true);

    const { initKeycloak } = await loadKeycloakModule();

    const [first, second] = await Promise.all([initKeycloak(), initKeycloak()]);
    expect(first).toBe(true);
    expect(second).toBe(true);
    expect(mockInstance.init).toHaveBeenCalledTimes(1);
    expect(mockInstance.init).toHaveBeenCalledWith(
      expect.objectContaining({
        onLoad: "check-sso",
        pkceMethod: "S256",
      })
    );
    const arg = mockInstance.init.mock.calls[0][0];
    expect(arg.silentCheckSsoRedirectUri).toContain("/silent-check-sso.html");
  });

  it("resets init promise after failure and allows retry", async () => {
    mockInstance.init.mockRejectedValueOnce(new Error("bootstrap failed")).mockResolvedValueOnce(true);

    const { initKeycloak } = await loadKeycloakModule();

    await expect(initKeycloak()).rejects.toThrow("bootstrap failed");
    await expect(initKeycloak()).resolves.toBe(true);
    expect(mockInstance.init).toHaveBeenCalledTimes(2);
  });

  it("returns null when user is not authenticated", async () => {
    mockInstance.authenticated = false;

    const { getToken } = await loadKeycloakModule();

    await expect(getToken()).resolves.toBeNull();
    expect(mockInstance.updateToken).not.toHaveBeenCalled();
  });

  it("refreshes and returns token when authenticated", async () => {
    mockInstance.authenticated = true;
    mockInstance.token = "token-123";
    mockInstance.updateToken.mockResolvedValue(true);

    const { getToken } = await loadKeycloakModule();

    await expect(getToken()).resolves.toBe("token-123");
    expect(mockInstance.updateToken).toHaveBeenCalledWith(30);
  });

  it("returns null when token refresh throws", async () => {
    mockInstance.authenticated = true;
    mockInstance.token = "token-123";
    mockInstance.updateToken.mockRejectedValue(new Error("refresh failed"));

    const { getToken } = await loadKeycloakModule();

    await expect(getToken()).resolves.toBeNull();
  });
});
