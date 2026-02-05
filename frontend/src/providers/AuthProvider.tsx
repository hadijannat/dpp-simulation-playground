import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { initKeycloak, keycloak } from "../services/keycloak";

interface AuthContextValue {
  initialized: boolean;
  authenticated: boolean;
  user: Record<string, unknown> | null;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  initialized: false,
  authenticated: false,
  user: null,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [initialized, setInitialized] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    initKeycloak().then((auth) => {
      setInitialized(true);
      setAuthenticated(auth);
      setUser((keycloak.tokenParsed as Record<string, unknown>) || null);
    });

    keycloak.onTokenExpired = () => {
      keycloak
        .updateToken(30)
        .then((refreshed) => {
          if (refreshed) {
            setUser((keycloak.tokenParsed as Record<string, unknown>) || null);
          }
        })
        .catch(() => {
          setAuthenticated(false);
          setUser(null);
        });
    };
  }, []);

  const value = useMemo(
    () => ({
      initialized,
      authenticated,
      user,
      login: () => keycloak.login(),
      logout: () => keycloak.logout({ redirectUri: window.location.origin }),
    }),
    [initialized, authenticated, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
