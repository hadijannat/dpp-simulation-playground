import { useState } from "react";
import { useTranslation } from "react-i18next";

const STORAGE_KEY = "dpp-ui-settings";

type UiSettings = {
  reduceMotion: boolean;
  compactDensity: boolean;
};

function loadSettings(): UiSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { reduceMotion: false, compactDensity: false };
    }
    return JSON.parse(raw) as UiSettings;
  } catch {
    return { reduceMotion: false, compactDensity: false };
  }
}

export default function SettingsPage() {
  const { t, i18n } = useTranslation("common");
  const [settings, setSettings] = useState<UiSettings>(() => loadSettings());
  const [saved, setSaved] = useState(false);

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    document.documentElement.style.setProperty("--motion-fast", settings.reduceMotion ? "0ms" : "140ms");
    document.documentElement.style.setProperty("--motion-medium", settings.reduceMotion ? "0ms" : "220ms");
    setSaved(true);
    setTimeout(() => setSaved(false), 1800);
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card">
        <h1>{t("settings")}</h1>
        <p>{t("settingsDescription")}</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>{t("localization")}</h3>
          <label>
            <div style={{ marginBottom: 6 }}>{t("language")}</div>
            <select className="input" value={i18n.language} onChange={(event) => i18n.changeLanguage(event.target.value)}>
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
            </select>
          </label>
        </div>

        <div className="card">
          <h3>{t("accessibilityUx")}</h3>
          <div style={{ display: "grid", gap: 8 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.reduceMotion}
                onChange={(event) =>
                  setSettings((current) => ({ ...current, reduceMotion: event.target.checked }))
                }
              />
              {t("reduceMotion")}
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.compactDensity}
                onChange={(event) =>
                  setSettings((current) => ({ ...current, compactDensity: event.target.checked }))
                }
              />
              {t("compactDensity")}
            </label>
            <button className="btn btn-primary" onClick={save}>{t("saveSettings")}</button>
            {saved && <span className="pill">{t("settingsSaved")}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
