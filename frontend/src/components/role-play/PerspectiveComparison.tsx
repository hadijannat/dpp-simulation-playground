export default function PerspectiveComparison({ left, right }: { left: string; right: string }) {
  return (
    <div className="grid-2">
      <div className="card-subtle">
        <h3>{left} View</h3>
        <p>Key tasks, visibility, and KPIs for this role.</p>
      </div>
      <div className="card-subtle">
        <h3>{right} View</h3>
        <p>Compare data requirements and compliance checkpoints side-by-side.</p>
      </div>
    </div>
  );
}
