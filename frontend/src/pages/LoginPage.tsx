import { useEffect } from "react";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();

  useEffect(() => {
    login();
  }, [login]);

  return (
    <div>
      <h1>Login</h1>
      <p>Redirecting to Keycloak...</p>
    </div>
  );
}
