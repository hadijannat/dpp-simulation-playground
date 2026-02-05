import { useState } from "react";
import MonacoWrapper from "../playground/MonacoWrapper";

export default function PolicyEditor() {
  const [policy, setPolicy] = useState(`{
  "permission": [
    {
      "constraint": {
        "leftOperand": "purpose",
        "rightOperand": "dpp:simulation"
      }
    }
  ]
}`);
  return (
    <div className="card">
      <div className="section-title">
        <h3>ODRL Policy Builder</h3>
        <span className="pill">Preview</span>
      </div>
      <MonacoWrapper value={policy} onChange={setPolicy} height={220} />
    </div>
  );
}
