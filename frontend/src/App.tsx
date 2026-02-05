import { Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import RouteGuard from "./components/common/RouteGuard";
import HomePage from "./pages/HomePage";
import JourneyPage from "./pages/JourneyPage";
import SimulationPage from "./pages/SimulationPage";
import PlaygroundPage from "./pages/PlaygroundPage";
import CompliancePage from "./pages/CompliancePage";
import EDCSimulatorPage from "./pages/EDCSimulatorPage";
import DashboardPage from "./pages/DashboardPage";
import AchievementsPage from "./pages/AchievementsPage";
import LeaderboardPage from "./pages/LeaderboardPage";
import GamificationPage from "./pages/GamificationPage";
import ComplianceReportsPage from "./pages/ComplianceReportsPage";
import SimulationSessionsPage from "./pages/SimulationSessionsPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import LoginPage from "./pages/LoginPage";
import CallbackPage from "./pages/CallbackPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/journey"
          element={
            <RouteGuard roles={["manufacturer", "developer", "admin"]}>
              <JourneyPage />
            </RouteGuard>
          }
        />
        <Route
          path="/simulation"
          element={
            <RouteGuard>
              <SimulationPage />
            </RouteGuard>
          }
        />
        <Route
          path="/simulation/sessions"
          element={
            <RouteGuard>
              <SimulationSessionsPage />
            </RouteGuard>
          }
        />
        <Route
          path="/playground"
          element={
            <RouteGuard>
              <PlaygroundPage />
            </RouteGuard>
          }
        />
        <Route
          path="/compliance"
          element={
            <RouteGuard roles={["manufacturer", "regulator", "developer", "admin"]}>
              <CompliancePage />
            </RouteGuard>
          }
        />
        <Route
          path="/compliance/reports"
          element={
            <RouteGuard roles={["regulator", "developer", "admin"]}>
              <ComplianceReportsPage />
            </RouteGuard>
          }
        />
        <Route
          path="/edc"
          element={
            <RouteGuard roles={["developer", "manufacturer", "admin"]}>
              <EDCSimulatorPage />
            </RouteGuard>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RouteGuard>
              <DashboardPage />
            </RouteGuard>
          }
        />
        <Route
          path="/gamification"
          element={
            <RouteGuard roles={["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]}>
              <GamificationPage />
            </RouteGuard>
          }
        />
        <Route
          path="/achievements"
          element={
            <RouteGuard roles={["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]}>
              <AchievementsPage />
            </RouteGuard>
          }
        />
        <Route
          path="/leaderboard"
          element={
            <RouteGuard roles={["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]}>
              <LeaderboardPage />
            </RouteGuard>
          }
        />
        <Route
          path="/profile"
          element={
            <RouteGuard>
              <ProfilePage />
            </RouteGuard>
          }
        />
        <Route
          path="/settings"
          element={
            <RouteGuard>
              <SettingsPage />
            </RouteGuard>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/callback" element={<CallbackPage />} />
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </AppShell>
  );
}
