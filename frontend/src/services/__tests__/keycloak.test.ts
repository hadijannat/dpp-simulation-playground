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

import { getToken, initKeycloak, keycloak } from "../keycloak";

describe("keycloak service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockInstance.authenticated = false;
    mockInstance.token = null;
  });

  it("initializes keycloak once with expected options", async () => {
    mockInstance.init.mockResolvedValue(true);

    const first = await initKeycloak();
    const second = await initKeycloak();

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

  it("returns null token when user is not authenticated", async () => {
    keycloak.authenticated = false;

    await expect(getToken()).resolves.toBeNull();
    expect(mockInstance.updateToken).not.toHaveBeenCalled();
  });

  it("refreshes and returns token when authenticated", async () => {
    keycloak.authenticated = true;
    keycloak.token = "jwt-token";
    mockInstance.updateToken.mockResolvedValue(true);

    await expect(getToken()).resolves.toBe("jwt-token");
    expect(mockInstance.updateToken).toHaveBeenCalledWith(30);
  });

  it("returns null when token refresh fails", async () => {
    keycloak.authenticated = true;
    keycloak.token = "stale-token";
    mockInstance.updateToken.mockRejectedValue(new Error("refresh failed"));

    await expect(getToken()).resolves.toBeNull();
    expect(mockInstance.updateToken).toHaveBeenCalledWith(30);
  });
});
