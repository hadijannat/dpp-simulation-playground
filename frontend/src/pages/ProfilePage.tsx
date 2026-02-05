import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import { useRoleStore } from "../stores/roleStore";

const STORAGE_KEY = "dpp-profile-preferences";

type Preferences = {
  organization: string;
  title: string;
  onboardingCompleted: boolean;
};

function loadPreferences(): Preferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { organization: "", title: "", onboardingCompleted: false };
    }
    return JSON.parse(raw) as Preferences;
  } catch {
    return { organization: "", title: "", onboardingCompleted: false };
  }
}

export default function ProfilePage() {
  const { t } = useTranslation("common");
  const { user } = useAuth();
  const { role } = useRoleStore();
  const [preferences, setPreferences] = useState<Preferences>(() => loadPreferences());
  const [savedAt, setSavedAt] = useState<string>("");

  const userId = useMemo(() => {
    const payload = user as { preferred_username?: string; email?: string; sub?: string } | null;
    return payload?.preferred_username || payload?.email || payload?.sub || "anonymous";
  }, [user]);

  function savePreferences() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    setSavedAt(new Date().toISOString());
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card">
        <h1>{t("profile")}</h1>
        <p>{t("profileDescription")}</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>{t("identity")}</h3>
          <div className="card-subtle">
            <div><strong>{t("user")}:</strong> {userId}</div>
            <div><strong>{t("activeRole")}:</strong> {role}</div>
          </div>
        </div>

        <div className="card">
          <h3>{t("preferences")}</h3>
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              <div style={{ marginBottom: 6 }}>{t("organization")}</div>
              <input
                className="input"
                value={preferences.organization}
                onChange={(event) =>
                  setPreferences((current) => ({ ...current, organization: event.target.value }))
                }
              />
            </label>

            <label>
              <div style={{ marginBottom: 6 }}>{t("title")}</div>
              <input
                className="input"
                value={preferences.title}
                onChange={(event) =>
                  setPreferences((current) => ({ ...current, title: event.target.value }))
                }
              />
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={preferences.onboardingCompleted}
                onChange={(event) =>
                  setPreferences((current) => ({
                    ...current,
                    onboardingCompleted: event.target.checked,
                  }))
                }
              />
              {t("onboardingCompleted")}
            </label>

            <button className="btn btn-primary" onClick={savePreferences}>{t("savePreferences")}</button>
            {savedAt && <span className="pill">{t("savedAt")} {savedAt}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
