import Keycloak from "keycloak-js";
import { keycloakConfig } from "../config/keycloak";

export const keycloak = new Keycloak({
  url: keycloakConfig.url,
  realm: keycloakConfig.realm,
  clientId: keycloakConfig.clientId,
});

export async function initKeycloak() {
  return keycloak.init({
    onLoad: "check-sso",
    pkceMethod: "S256",
    silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
  });
}

export async function getToken() {
  if (!keycloak.authenticated) return null;
  try {
    await keycloak.updateToken(30);
  } catch (err) {
    return null;
  }
  return keycloak.token ?? null;
}
