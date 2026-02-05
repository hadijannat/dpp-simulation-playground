import { useState } from "react";
import MonacoWrapper from "../playground/MonacoWrapper";

export default function PolicyEditor() {
  const [policy, setPolicy] = useState(`{\n  \"permission\": [\n    {\n      \"constraint\": {\n        \"leftOperand\": \"purpose\",\n        \"rightOperand\": \"dpp:simulation\"\n      }\n    }\n  ]\n}`);
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
