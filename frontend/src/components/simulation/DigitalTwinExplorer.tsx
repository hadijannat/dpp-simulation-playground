import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  DigitalTwin,
  DigitalTwinDiffResponse,
  DigitalTwinHistoryResponse,
  DigitalTwinNode,
} from "../../types/v2.types";

interface DigitalTwinExplorerProps {
  twin?: DigitalTwin | null;
  history?: DigitalTwinHistoryResponse | null;
  diff?: DigitalTwinDiffResponse | null;
  historyLoading?: boolean;
  diffLoading?: boolean;
  fromSnapshotIndex: number;
  toSnapshotIndex: number;
  onFromSnapshotIndexChange: (index: number) => void;
  onToSnapshotIndexChange: (index: number) => void;
}

type PositionedNode = DigitalTwinNode & { x: number; y: number };

function nodeColor(type?: string): string {
  if (type === "asset" || type === "product") return "#00e8ff";
  if (type === "status" || type === "compliance") return "#00ff9c";
  if (type === "dataspace" || type === "transfer") return "#ffb347";
  return "#91b6ff";
}

function summarizeRecord(item: Record<string, unknown>, fallback: string): string {
  const id = item.id;
  if (typeof id === "string" && id.length > 0) return id;
  const label = item.label;
  if (typeof label === "string" && label.length > 0) return label;
  const key = item.key;
  if (typeof key === "string" && key.length > 0) return key;
  return fallback;
}

export default function DigitalTwinExplorer({
  twin,
  history,
  diff,
  historyLoading = false,
  diffLoading = false,
  fromSnapshotIndex,
  toSnapshotIndex,
  onFromSnapshotIndexChange,
  onToSnapshotIndexChange,
}: DigitalTwinExplorerProps) {
  const { t } = useTranslation("journey");
  const [selectedType, setSelectedType] = useState("all");

  const historyItems = history?.items || [];
  const maxHistoryIndex = Math.max(historyItems.length - 1, 0);
  const safeFromIndex = Math.max(0, Math.min(fromSnapshotIndex, maxHistoryIndex));
  const safeToIndex = Math.max(safeFromIndex, Math.min(toSnapshotIndex, maxHistoryIndex));

  const nodeTypes = useMemo(
    () => Array.from(new Set((twin?.nodes || []).map((node) => node.type).filter(Boolean))).sort(),
    [twin?.nodes],
  );
  const activeFilter = nodeTypes.includes(selectedType) ? selectedType : "all";

  const filteredNodes = useMemo(() => {
    const nodes = twin?.nodes || [];
    if (activeFilter === "all") return nodes;
    return nodes.filter((node) => node.type === activeFilter);
  }, [activeFilter, twin?.nodes]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((node) => node.id)), [filteredNodes]);

  const filteredEdges = useMemo(
    () => (twin?.edges || []).filter((edge) => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)),
    [filteredNodeIds, twin?.edges],
  );

  const positionedNodes = useMemo<PositionedNode[]>(() => {
    if (filteredNodes.length === 0) return [];
    const width = 720;
    const height = 320;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 54;

    return filteredNodes.map((node, index) => {
      if (filteredNodes.length === 1) return { ...node, x: centerX, y: centerY };
      const angle = ((Math.PI * 2) / filteredNodes.length) * index - Math.PI / 2;
      return {
        ...node,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      };
    });
  }, [filteredNodes]);

  const nodePositionById = useMemo(
    () => new Map(positionedNodes.map((node) => [node.id, node])),
    [positionedNodes],
  );

  const fromSnapshot = historyItems[safeFromIndex];
  const toSnapshot = historyItems[safeToIndex];

  return (
    <div className="digital-twin-layout">
      <div className="card-subtle">
        <div className="section-title">
          <h2>{t("digitalTwinGraphTitle")}</h2>
          <label className="digital-twin-filter">
            <span>{t("digitalTwinFilterLabel")}</span>
            <select
              value={activeFilter}
              onChange={(event) => setSelectedType(event.target.value)}
              aria-label={t("digitalTwinFilterLabel")}
            >
              <option value="all">{t("digitalTwinFilterAll")}</option>
              {nodeTypes.map((typeName) => (
                <option key={typeName} value={typeName}>
                  {typeName}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="digital-twin-graph">
          {positionedNodes.length === 0 ? (
            <div className="pill">{t("digitalTwinNoNodes")}</div>
          ) : (
            <svg
              className="digital-twin-svg"
              viewBox="0 0 720 320"
              role="img"
              aria-label={t("digitalTwinGraphAria")}
            >
              <defs>
                <marker id="dt-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto-start-reverse">
                  <path d="M0,0 L8,4 L0,8 z" fill="#6ea6ff" />
                </marker>
              </defs>

              {filteredEdges.map((edge, index) => {
                const source = nodePositionById.get(edge.source);
                const target = nodePositionById.get(edge.target);
                if (!source || !target) return null;
                const midX = (source.x + target.x) / 2;
                const midY = (source.y + target.y) / 2;
                const edgeLabel = "label" in edge && typeof edge.label === "string" ? edge.label : undefined;
                return (
                  <g key={`${edge.id}-${index}`}>
                    <line
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke="#5d8ad6"
                      strokeWidth="1.6"
                      markerEnd="url(#dt-arrow)"
                      opacity="0.85"
                    />
                    {edgeLabel ? (
                      <text x={midX} y={midY - 8} className="digital-twin-edge-label">
                        {edgeLabel}
                      </text>
                    ) : null}
                  </g>
                );
              })}

              {positionedNodes.map((node) => (
                <g key={node.id}>
                  <circle cx={node.x} cy={node.y} r="28" fill={nodeColor(node.type)} fillOpacity="0.24" stroke={nodeColor(node.type)} strokeWidth="1.8" />
                  <text x={node.x} y={node.y - 2} textAnchor="middle" className="digital-twin-node-title">
                    {node.label}
                  </text>
                  <text x={node.x} y={node.y + 12} textAnchor="middle" className="digital-twin-node-type">
                    {node.type}
                  </text>
                </g>
              ))}
            </svg>
          )}
        </div>
      </div>

      <div className="card-subtle">
        <div className="section-title">
          <h2>{t("digitalTwinTimelineTitle")}</h2>
          <span className="pill">{history?.total || 0}</span>
        </div>

        {historyLoading ? (
          <div>{t("digitalTwinLoadingHistory")}</div>
        ) : historyItems.length === 0 ? (
          <div className="pill">{t("digitalTwinNoHistory")}</div>
        ) : (
          <>
            <div className="digital-twin-slider-grid">
              <label>
                <div>{t("digitalTwinFromSnapshot")}</div>
                <input
                  type="range"
                  min={0}
                  max={maxHistoryIndex}
                  value={safeFromIndex}
                  onChange={(event) => onFromSnapshotIndexChange(Number(event.target.value))}
                  aria-label={t("digitalTwinFromSnapshot")}
                />
              </label>
              <label>
                <div>{t("digitalTwinToSnapshot")}</div>
                <input
                  type="range"
                  min={0}
                  max={maxHistoryIndex}
                  value={safeToIndex}
                  onChange={(event) => onToSnapshotIndexChange(Number(event.target.value))}
                  aria-label={t("digitalTwinToSnapshot")}
                />
              </label>
            </div>
            <div className="digital-twin-chip-list">
              {fromSnapshot ? (
                <span className="digital-twin-chip">
                  {t("digitalTwinFromSnapshot")} · {fromSnapshot.label || fromSnapshot.snapshot_id}
                </span>
              ) : null}
              {toSnapshot ? (
                <span className="digital-twin-chip">
                  {t("digitalTwinToSnapshot")} · {toSnapshot.label || toSnapshot.snapshot_id}
                </span>
              ) : null}
            </div>
          </>
        )}
      </div>

      <div className="card-subtle">
        <div className="section-title">
          <h2>{t("digitalTwinDiffTitle")}</h2>
          {diff?.diff?.generated_at ? <span className="pill">{diff.diff.generated_at}</span> : null}
        </div>

        {historyItems.length < 2 || safeFromIndex === safeToIndex ? (
          <div className="pill">{t("digitalTwinDiffSelectRange")}</div>
        ) : diffLoading ? (
          <div>{t("digitalTwinLoadingDiff")}</div>
        ) : !diff ? (
          <div>{t("digitalTwinNoDiff")}</div>
        ) : (
          <>
            <div className="digital-twin-diff-grid">
              <div>
                <div className="digital-twin-metric">{t("digitalTwinNodesAdded")}</div>
                <strong>{diff.diff.summary.nodes_added}</strong>
              </div>
              <div>
                <div className="digital-twin-metric">{t("digitalTwinNodesChanged")}</div>
                <strong>{diff.diff.summary.nodes_changed}</strong>
              </div>
              <div>
                <div className="digital-twin-metric">{t("digitalTwinNodesRemoved")}</div>
                <strong>{diff.diff.summary.nodes_removed}</strong>
              </div>
              <div>
                <div className="digital-twin-metric">{t("digitalTwinEdgesAdded")}</div>
                <strong>{diff.diff.summary.edges_added}</strong>
              </div>
              <div>
                <div className="digital-twin-metric">{t("digitalTwinEdgesChanged")}</div>
                <strong>{diff.diff.summary.edges_changed}</strong>
              </div>
              <div>
                <div className="digital-twin-metric">{t("digitalTwinEdgesRemoved")}</div>
                <strong>{diff.diff.summary.edges_removed}</strong>
              </div>
            </div>

            {(diff.diff.nodes.changed.length > 0 || diff.diff.edges.changed.length > 0) && (
              <div className="digital-twin-change-grid">
                {diff.diff.nodes.changed.length > 0 && (
                  <div>
                    <h4>{t("digitalTwinChangedNodes")}</h4>
                    <ul>
                      {diff.diff.nodes.changed.map((item) => (
                        <li key={item.key}>{item.key}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {diff.diff.edges.changed.length > 0 && (
                  <div>
                    <h4>{t("digitalTwinChangedEdges")}</h4>
                    <ul>
                      {diff.diff.edges.changed.map((item) => (
                        <li key={item.key}>{item.key}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {(diff.diff.nodes.added.length > 0 || diff.diff.edges.added.length > 0) && (
              <div className="digital-twin-change-grid">
                {diff.diff.nodes.added.length > 0 && (
                  <div>
                    <h4>{t("digitalTwinAddedNodes")}</h4>
                    <ul>
                      {diff.diff.nodes.added.slice(0, 6).map((item, index) => (
                        <li key={`node-added-${index}`}>{summarizeRecord(item, `node-${index + 1}`)}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {diff.diff.edges.added.length > 0 && (
                  <div>
                    <h4>{t("digitalTwinAddedEdges")}</h4>
                    <ul>
                      {diff.diff.edges.added.slice(0, 6).map((item, index) => (
                        <li key={`edge-added-${index}`}>{summarizeRecord(item, `edge-${index + 1}`)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
