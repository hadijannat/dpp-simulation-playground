import { ReactNode } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import "./app-shell.css";

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <div className="app-content">{children}</div>
      </div>
    </div>
  );
}
