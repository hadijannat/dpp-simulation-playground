import { useState } from "react";

interface StoryStep {
  action: string;
  params?: Record<string, unknown>;
}

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
  const [payloads, setPayloads] = useState<Record<number, string>>({});

  function parsedPayload(value: string) {
    try {
      return JSON.parse(value);
    } catch {
      return null;
    }
  }

  return (
    <div className="card">
      <div className="section-title">
        <h3>Step Executor</h3>
        <span className="pill">{storyCode}</span>
      </div>
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {steps.map((step, idx) => {
          const template = defaultPayloadForAction(step.action);
          const text = payloads[idx] ?? JSON.stringify(template, null, 2);
          const parsed = parsedPayload(text);

          return (
            <div key={`${step.action}-${idx}`} className="card-subtle">
              <div style={{ fontWeight: 600 }}>{idx + 1}. {step.action}</div>
              {step.params && <pre>{JSON.stringify(step.params, null, 2)}</pre>}
              <textarea
                className="textarea"
                rows={6}
                value={text}
                onChange={(e) => setPayloads((prev) => ({ ...prev, [idx]: e.target.value }))}
              />
              {!parsed && <div style={{ color: "#b91c1c" }}>Invalid JSON payload</div>}
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
          );
        })}
      </div>
    </div>
  );
}
