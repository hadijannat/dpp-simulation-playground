import Keycloak from "keycloak-js";
import { keycloakConfig } from "../config/keycloak";

export const keycloak = new Keycloak({
  url: keycloakConfig.url,
  realm: keycloakConfig.realm,
  clientId: keycloakConfig.clientId,
});

let initPromise: Promise<boolean> | null = null;

export async function initKeycloak() {
  if (initPromise) {
    return initPromise;
  }
  initPromise = keycloak
    .init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
    })
    .catch((err) => {
      initPromise = null;
      throw err;
    });
  return initPromise;
}

export async function getToken() {
  if (!keycloak.authenticated) return null;
  try {
    await keycloak.updateToken(30);
  } catch {
    return null;
  }
  return keycloak.token ?? null;
}
