interface StoryItem {
  code: string;
  title: string;
  epic_code?: string;
}

export default function StoryNavigator({
  stories,
  selectedCode,
  onSelect,
}: {
  stories: StoryItem[];
  selectedCode: string;
  onSelect: (code: string) => void;
}) {
  const grouped = stories.reduce<Record<string, StoryItem[]>>((acc, story) => {
    const epic = story.epic_code || "EPIC-Unknown";
    if (!acc[epic]) acc[epic] = [];
    acc[epic].push(story);
    return acc;
  }, {});

  return (
    <div className="card-subtle">
      <div className="section-title">
        <h3>Scenarios</h3>
      </div>
      {Object.entries(grouped).map(([epic, items]) => (
        <div key={epic} style={{ marginBottom: 12 }}>
          <div className="pill">{epic}</div>
          <div style={{ display: "grid", gap: 6, marginTop: 8 }}>
            {items.map((story) => (
              <button
                key={story.code}
                className="btn btn-secondary"
                style={{
                  textAlign: "left",
                  background: selectedCode === story.code ? "var(--canvas-node-selected)" : undefined,
                }}
                onClick={() => onSelect(story.code)}
              >
                {story.code} · {story.title}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
