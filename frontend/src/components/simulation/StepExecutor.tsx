import { useState } from "react";

interface StoryStep {
  action: string;
  params?: Record<string, unknown>;
}

type DraftState = {
  present: string;
  past: string[];
};

const ACTION_HINTS: Record<string, string> = {
  "aas.create": "Include aas_identifier and product identifiers to avoid downstream validation failures.",
  "compliance.check": "Provide regulations and payload data for deterministic compliance output.",
  "edc.negotiate": "Use participant IDs and policy purpose aligned with your business context.",
  "edc.transfer": "Keep asset and participant references consistent with negotiation results.",
  "aas.submodel.add": "Start with a small submodel to validate schema compatibility quickly.",
  "aasx.upload": "Large base64 payloads may impact browser responsiveness.",
};

function defaultPayloadForAction(action: string) {
  switch (action) {
    case "aas.create":
      return {
        product_name: "Sample Product",
        product_category: "battery",
        templates: ["DigitalNameplate"],
      };
    case "compliance.check":
      return { regulations: ["ESPR"], data: {} };
    case "edc.negotiate":
      return {
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        asset_id: "asset-001",
        policy: {
          "@type": "odrl:Offer",
          permission: [
            {
              action: "use",
              constraint: {
                leftOperand: "purpose",
                operator: "eq",
                rightOperand: "compliance-verification",
              },
            },
          ],
        },
      };
    case "edc.transfer":
      return {
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
      };
    case "aas.submodel.add":
      return { submodel: { idShort: "Submodel", submodelElements: [] } };
    case "aas.submodel.patch":
      return { submodel_id: "submodel-id", elements: [] };
    case "aas.update":
      return { update: "manual-update", data: {} };
    case "aasx.upload":
      return { filename: "dpp.aasx", content_base64: "" };
    default:
      return {};
  }
}

export default function StepExecutor({
  storyCode,
  steps,
  onExecute,
}: {
  storyCode: string;
  steps: StoryStep[];
  onExecute: (idx: number, payload: Record<string, unknown>) => void;
}) {
  const [payloads, setPayloads] = useState<Record<number, DraftState>>({});

  function parsedPayload(value: string) {
    try {
      return JSON.parse(value);
    } catch {
      return null;
    }
  }

  function getDraft(idx: number, action: string) {
    return payloads[idx] ?? {
      present: JSON.stringify(defaultPayloadForAction(action), null, 2),
      past: [],
    };
  }

  function setDraft(idx: number, next: string) {
    setPayloads((current) => {
      const previous =
        current[idx] ?? {
          present: JSON.stringify(defaultPayloadForAction(steps[idx].action), null, 2),
          past: [],
        };
      return {
        ...current,
        [idx]: {
          present: next,
          past: [...previous.past, previous.present],
        },
      };
    });
  }

  function undoDraft(idx: number, action: string) {
    setPayloads((current) => {
      const previous =
        current[idx] ?? {
          present: JSON.stringify(defaultPayloadForAction(action), null, 2),
          past: [],
        };
      if (previous.past.length === 0) {
        return current;
      }
      const nextPresent = previous.past[previous.past.length - 1];
      return {
        ...current,
        [idx]: {
          present: nextPresent,
          past: previous.past.slice(0, -1),
        },
      };
    });
  }

  return (
    <div className="card">
      <div className="section-title">
        <h3>Step Executor</h3>
        <span className="pill">{storyCode}</span>
      </div>
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {steps.map((step, idx) => {
          const draft = getDraft(idx, step.action);
          const text = draft.present;
          const parsed = parsedPayload(text);
          const hint = ACTION_HINTS[step.action] || "Review payload structure before executing this step.";

          return (
            <div key={`${step.action}-${idx}`} className="card-subtle">
              <div style={{ fontWeight: 600 }}>{idx + 1}. {step.action}</div>
              <div className="pill" style={{ marginBottom: 8 }}>{hint}</div>
              {step.params && <pre className="mono-panel">{JSON.stringify(step.params, null, 2)}</pre>}
              <textarea
                className="textarea"
                rows={6}
                value={text}
                onChange={(e) => setDraft(idx, e.target.value)}
              />
              {!parsed && <div className="error">Invalid JSON payload</div>}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button className="btn btn-secondary" onClick={() => undoDraft(idx, step.action)} disabled={draft.past.length === 0}>
                  Undo
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    if (!parsed) return;
                    onExecute(idx, parsed);
                  }}
                >
                  Execute Step
                </button>
              </div>
              <div style={{ marginTop: 8 }}>
                <div style={{ color: "var(--ink-muted)", fontSize: 12, marginBottom: 6 }}>Payload Preview</div>
                <pre className="mono-panel">{JSON.stringify(parsed || {}, null, 2)}</pre>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
