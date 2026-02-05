import { Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import HomePage from "./pages/HomePage";
import SimulationPage from "./pages/SimulationPage";
import PlaygroundPage from "./pages/PlaygroundPage";
import CompliancePage from "./pages/CompliancePage";
import EDCSimulatorPage from "./pages/EDCSimulatorPage";
import DashboardPage from "./pages/DashboardPage";
import AchievementsPage from "./pages/AchievementsPage";
import LeaderboardPage from "./pages/LeaderboardPage";
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
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/playground" element={<PlaygroundPage />} />
        <Route path="/compliance" element={<CompliancePage />} />
        <Route path="/edc" element={<EDCSimulatorPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/achievements" element={<AchievementsPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/callback" element={<CallbackPage />} />
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </AppShell>
  );
}
