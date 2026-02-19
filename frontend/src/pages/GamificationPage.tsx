import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useGamification } from "../hooks/useGamification";
import { useRoleStore } from "../stores/roleStore";
import { useGamificationStore } from "../stores/gamificationStore";
import type { Achievement, LeaderboardWindow, StreakEntry } from "../types/api.types";

const WINDOW_OPTIONS: LeaderboardWindow[] = ["all", "daily", "weekly", "monthly"];
const ROLE_OPTIONS = ["all", "manufacturer", "regulator", "consumer", "recycler", "developer", "admin"] as const;

const WINDOW_LABEL_KEYS: Record<LeaderboardWindow, string> = {
  all: "windowAll",
  daily: "windowDaily",
  weekly: "windowWeekly",
  monthly: "windowMonthly",
};

type ToastItem = {
  id: string;
  message: string;
};

export default function GamificationPage() {
  const { t } = useTranslation("gamification");
  const { role: activeRole } = useRoleStore();
  const [windowFilter, setWindowFilter] = useState<LeaderboardWindow>("all");
  const [roleFilter, setRoleFilter] = useState<(typeof ROLE_OPTIONS)[number]>("all");
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const seenAchievementCodesRef = useRef<Set<string>>(new Set());
  const initializedAchievementsRef = useRef(false);

  const queryRole = roleFilter === "all" ? undefined : roleFilter;
  const { achievements, leaderboard, streaks } = useGamification({
    limit: 20,
    window: windowFilter,
    role: queryRole,
  });

  const storedLeaderboard = useGamificationStore((state) => state.leaderboard);
  const leaderboardItems = leaderboard.data?.items ?? storedLeaderboard;
  const streakItems = streaks.data?.items || [];
  const topEntry = leaderboardItems[0];

  const streakByUserId = useMemo(() => {
    const next = new Map<string, StreakEntry>();
    streakItems.forEach((item) => next.set(item.user_id, item));
    return next;
  }, [streakItems]);

  useEffect(() => {
    const items: Achievement[] = achievements.data?.items || [];
    const codes = items.map((item) => item.code).filter(Boolean);
    if (!initializedAchievementsRef.current) {
      codes.forEach((code) => seenAchievementCodesRef.current.add(code));
      initializedAchievementsRef.current = true;
      return;
    }
    const newCodes = codes.filter((code) => !seenAchievementCodesRef.current.has(code));
    if (newCodes.length === 0) return;

    const now = Date.now();
    const notifications = newCodes.slice(0, 3).map((code, index) => {
      const achievement = items.find((item) => item.code === code);
      return {
        id: `${now}-${index}-${code}`,
        message: t("newAchievementToast", { name: achievement?.name || code }),
      };
    });
    newCodes.forEach((code) => seenAchievementCodesRef.current.add(code));
    setToasts((current) => [...current, ...notifications]);
  }, [achievements.data?.items, t]);

  useEffect(() => {
    if (toasts.length === 0) return;
    const timer = window.setTimeout(() => {
      setToasts((current) => current.slice(1));
    }, 3500);
    return () => window.clearTimeout(timer);
  }, [toasts]);

  return (
    <div className="page" style={{ display: "grid", gap: 16 }}>
      <div className="section-title">
        <h2>{t("title")}</h2>
        <span className="pill">{t("activeRole")}: {activeRole}</span>
      </div>

      <div className="card gamification-toolbar">
        <label>
          <div>{t("windowLabel")}</div>
          <select
            value={windowFilter}
            onChange={(event) => setWindowFilter(event.target.value as LeaderboardWindow)}
            aria-label={t("windowLabel")}
          >
            {WINDOW_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {t(WINDOW_LABEL_KEYS[option])}
              </option>
            ))}
          </select>
        </label>
        <label>
          <div>{t("roleLabel")}</div>
          <select
            value={roleFilter}
            onChange={(event) => setRoleFilter(event.target.value as (typeof ROLE_OPTIONS)[number])}
            aria-label={t("roleLabel")}
          >
            {ROLE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option === "all" ? t("allRoles") : option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="gamification-summary-grid">
        <div className="card">
          <div className="digital-twin-metric">{t("topScore")}</div>
          <h3>{topEntry ? `${topEntry.total_points} ${t("pts")}` : "--"}</h3>
          <div style={{ color: "var(--ink-secondary)" }}>
            {topEntry ? `${topEntry.user_id} · ${t("level")} ${topEntry.level}` : t("noLeaderboard")}
          </div>
        </div>
        <div className="card">
          <div className="digital-twin-metric">{t("leaderboardContext")}</div>
          <h3>{leaderboard.data?.window || windowFilter}</h3>
          <div style={{ color: "var(--ink-secondary)" }}>
            {leaderboard.data?.role || queryRole || t("allRoles")}
          </div>
        </div>
        <div className="card">
          <div className="digital-twin-metric">{t("streaks")}</div>
          <h3>{streakItems.length}</h3>
          <div style={{ color: "var(--ink-secondary)" }}>
            {topEntry && streakByUserId.get(topEntry.user_id)
              ? `${t("longest")}: ${streakByUserId.get(topEntry.user_id)?.longest_streak_days} ${t("days")}`
              : t("noStreaks")}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>{t("achievements")}</h3>
          {achievements.isLoading && <div>{t("loadingAchievements")}</div>}
          {achievements.error && <div className="error">{t("loadingAchievementsError")}</div>}
          {achievements.data?.items?.length ? (
            <div style={{ display: "grid", gap: 10 }}>
              {achievements.data.items.slice(0, 8).map((item: Achievement, idx: number) => (
                <div key={`${item.code ?? idx}`} className="card-subtle">
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <strong>{item.name ?? item.code}</strong>
                    <span className="pill">+{item.points || 0} {t("pts")}</span>
                  </div>
                  <div style={{ color: "var(--ink-secondary)" }}>
                    {item.description || item.code}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            !achievements.isLoading && <div>{t("noAchievements")}</div>
          )}
        </div>

        <div className="card">
          <h3>{t("leaderboard")}</h3>
          {leaderboard.isLoading && <div>{t("loadingLeaderboard")}</div>}
          {leaderboard.error && <div className="error">{t("loadingLeaderboardError")}</div>}
          {leaderboardItems.length ? (
            <table className="table">
              <thead>
                <tr>
                  <th>{t("user")}</th>
                  <th>{t("points")}</th>
                  <th>{t("level")}</th>
                  <th>{t("roleLabel")}</th>
                </tr>
              </thead>
              <tbody>
                {leaderboardItems.map((entry) => (
                  <tr key={entry.user_id}>
                    <td>{entry.user_id}</td>
                    <td>{entry.total_points}</td>
                    <td>{entry.level}</td>
                    <td>{entry.role || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            !leaderboard.isLoading && <div>{t("noLeaderboard")}</div>
          )}
        </div>
      </div>

      <div className="card">
        <h3>{t("streaks")}</h3>
        {streaks.isLoading && <div>{t("loadingStreaks")}</div>}
        {streaks.error && <div className="error">{t("loadingStreaksError")}</div>}
        {streakItems.length ? (
          <div style={{ display: "grid", gap: 10 }}>
            {streakItems.map((item) => (
              <div key={item.user_id} className="card-subtle" style={{ display: "flex", justifyContent: "space-between" }}>
                <div>{item.user_id}</div>
                <div>
                  <strong>{item.current_streak_days} {t("days")}</strong>
                  <span style={{ marginLeft: 12, color: "var(--ink-muted)" }}>
                    {t("longest")}: {item.longest_streak_days}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          !streaks.isLoading && <div>{t("noStreaks")}</div>
        )}
      </div>

      <div className="gamification-toast-stack" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className="gamification-toast">
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}
