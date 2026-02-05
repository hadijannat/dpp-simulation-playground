import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useRoleStore } from "../stores/roleStore";
import { useSessionStore } from "../stores/sessionStore";

export default function HomePage() {
  const navigate = useNavigate();
  const { t } = useTranslation(["common", "simulation", "compliance", "edc"]);
  const { role } = useRoleStore();
  const currentSession = useSessionStore((state) => state.currentSession);
  const currentJourneyRunId = useSessionStore((state) => state.currentJourneyRunId);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card hero-panel">
        <h1>{t("appTitle")}</h1>
        <p>
          Manufacturer-first DPP simulation with role switching, compliance workflows, and dataspace negotiation flows.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={() => navigate("/journey")}>
            Start Manufacturer Journey
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/simulation")}>
            {t("simulation:title")}
          </button>
          {currentJourneyRunId && (
            <button className="btn btn-secondary" onClick={() => navigate("/journey")}>
              Continue Journey
            </button>
          )}
          {currentSession && (
            <button className="btn btn-secondary" onClick={() => navigate("/simulation")}>
              {t("simulation:resumeSession")}
            </button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="section-title">
          <h3>First-Run Onboarding</h3>
          <span className="pill">{t("role")}: {role}</span>
        </div>
        <ol className="onboarding-list">
          <li>Start with the Manufacturer Journey to generate a DPP shell and payload baseline.</li>
          <li>Run compliance checks, apply fixes, and revalidate immediately.</li>
          <li>Simulate EDC negotiation and transfer to test dataspace readiness.</li>
        </ol>
      </div>

      <p>
        Learn, validate, and stress-test Digital Product Passport workflows using real AAS payloads, compliance
        validation, and simulated dataspace negotiations.
      </p>
      <div className="grid-3" style={{ marginTop: 16 }}>
        <div className="card-subtle">
          <h3>{t("simulation:title")}</h3>
          <p>Run end-to-end stories across roles and track progress.</p>
        </div>
        <div className="card-subtle">
          <h3>{t("compliance:title")}</h3>
          <p>Evaluate ESPR, Battery Regulation, WEEE, and RoHS checks.</p>
        </div>
        <div className="card-subtle">
          <h3>{t("edc:title")}</h3>
          <p>Negotiate contracts and model data transfer state machines.</p>
        </div>
      </div>
    </div>
  );
}
