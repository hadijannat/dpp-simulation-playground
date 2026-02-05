export default function PerspectiveComparison({ left, right }: { left: string; right: string }) {
  return (
    <div className="grid-2">
      <div className="card-subtle">
        <h4>{left} View</h4>
        <p>Key tasks, visibility, and KPIs for this role.</p>
      </div>
      <div className="card-subtle">
        <h4>{right} View</h4>
        <p>Compare data requirements and compliance checkpoints side-by-side.</p>
      </div>
    </div>
  );
}
