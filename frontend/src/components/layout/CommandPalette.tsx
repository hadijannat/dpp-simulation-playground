import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

type Command = {
  id: string;
  label: string;
  hint?: string;
  action: () => void;
};

export default function CommandPalette() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const commands = useMemo<Command[]>(
    () => [
      { id: "home", label: "Go to Home", hint: "Overview and onboarding", action: () => navigate("/") },
      { id: "journey", label: "Start Manufacturer Journey", hint: "Guided core flow", action: () => navigate("/journey") },
      { id: "simulation", label: "Open Simulation", hint: "Story execution workspace", action: () => navigate("/simulation") },
      { id: "playground", label: "Open API Playground", hint: "Direct API testing", action: () => navigate("/playground") },
      { id: "compliance", label: "Open Compliance", hint: "Run and review checks", action: () => navigate("/compliance") },
      { id: "edc", label: "Open EDC Simulator", hint: "Negotiation and transfer", action: () => navigate("/edc") },
      { id: "profile", label: "Open Profile", hint: "Persona preferences", action: () => navigate("/profile") },
      { id: "settings", label: "Open Settings", hint: "Language and UX settings", action: () => navigate("/settings") },
    ],
    [navigate],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const hotkey = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      if (hotkey) {
        event.preventDefault();
        setOpen((prev) => !prev);
      }
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!open) {
      setQuery("");
    }
  }, [open]);

  const filtered = commands.filter((command) => {
    const haystack = `${command.label} ${command.hint || ""}`.toLowerCase();
    return haystack.includes(query.toLowerCase());
  });

  if (!open) {
    return null;
  }

  return (
    <div className="cmdk-overlay" onClick={() => setOpen(false)} role="presentation">
      <div className="cmdk-modal" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
        <div style={{ padding: 12, borderBottom: "1px solid rgba(25, 51, 84, 0.75)" }}>
          <input
            className="input"
            autoFocus
            placeholder="Type a command..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Command palette query"
          />
        </div>
        <div className="cmdk-list">
          {filtered.map((command) => (
            <button
              key={command.id}
              className="cmdk-item"
              onClick={() => {
                command.action();
                setOpen(false);
              }}
            >
              <div style={{ fontWeight: 600 }}>{command.label}</div>
              {command.hint && <div style={{ color: "var(--ink-muted)", fontSize: 13, marginTop: 4 }}>{command.hint}</div>}
            </button>
          ))}
          {filtered.length === 0 && <div style={{ padding: 14, color: "var(--ink-muted)" }}>No matching command</div>}
        </div>
      </div>
    </div>
  );
}
