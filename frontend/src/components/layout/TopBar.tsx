import RoleSelector from "../common/RoleSelector";
import { useAuth } from "../../hooks/useAuth";
import { useTranslation } from "react-i18next";

export default function TopBar() {
  const { initialized, authenticated, login, logout } = useAuth();
  const { t, i18n } = useTranslation("common");

  return (
    <header className="topbar">
      <div>
        <div className="topbar-title">{t("appTitle")}</div>
        <div style={{ color: "var(--ink-muted)", fontSize: 12 }}>{t("commandPaletteHint")}</div>
      </div>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--ink-muted)" }}>{t("language")}</span>
          <select
            className="input"
            style={{ width: 82, padding: "8px 10px" }}
            value={i18n.language}
            onChange={(event) => i18n.changeLanguage(event.target.value)}
            aria-label={t("language")}
          >
            <option value="en">EN</option>
            <option value="de">DE</option>
            <option value="fr">FR</option>
          </select>
        </label>
        <RoleSelector />
        {!initialized ? (
          <span className="pill">Auth...</span>
        ) : authenticated ? (
          <button className="btn btn-secondary" onClick={logout}>{t("logout")}</button>
        ) : (
          <button className="btn btn-primary" onClick={login}>{t("login")}</button>
        )}
      </div>
    </header>
  );
}
