export default function HomePage() {
  return (
    <div>
      <h1>DPP Simulation Playground</h1>
      <p>
        Learn, validate, and stress-test Digital Product Passport workflows using real AAS payloads, compliance
        validation, and simulated dataspace negotiations.
      </p>
      <div className="grid-3" style={{ marginTop: 16 }}>
        <div className="card-subtle">
          <h3>Simulation</h3>
          <p>Run end-to-end stories across roles and track progress.</p>
        </div>
        <div className="card-subtle">
          <h3>Compliance</h3>
          <p>Evaluate ESPR, Battery Regulation, WEEE, and RoHS checks.</p>
        </div>
        <div className="card-subtle">
          <h3>EDC</h3>
          <p>Negotiate contracts and model data transfer state machines.</p>
        </div>
      </div>
    </div>
  );
}
