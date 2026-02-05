export const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: "dpp",
  clientId: "dpp-frontend",
};
