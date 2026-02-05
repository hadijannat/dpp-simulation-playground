import { useEDC } from "../../hooks/useEDC";

interface CatalogAsset {
  id: string;
  name?: string;
  title?: string;
  description?: string;
}

export default function CatalogBrowser() {
  const { catalog } = useEDC();
  const items = (catalog.data?.dataset || []) as CatalogAsset[];

  return (
    <div className="card">
      <div className="section-title">
        <h3>EDC Catalog</h3>
        <span className="pill">{items.length} assets</span>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {items.map((asset) => (
          <div key={asset.id} className="card-subtle">
            <div style={{ fontWeight: 600 }}>{asset.name || asset.title || asset.id}</div>
            <div style={{ color: "#64748b" }}>{asset.description || "Policy attached"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
