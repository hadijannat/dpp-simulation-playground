import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../services/api";

export default function AnnotationLayer({ storyId }: { storyId?: number }) {
  const [items, setItems] = useState<any[]>([]);
  const [content, setContent] = useState("");

  async function load() {
    const data = await apiGet(`/api/v1/annotations${storyId ? `?story_id=${storyId}` : ""}`);
    setItems(data.items || []);
  }

  async function add() {
    if (!content.trim()) return;
    const data = await apiPost("/api/v1/annotations", {
      story_id: storyId,
      annotation_type: "comment",
      content,
    });
    setItems([data, ...items]);
    setContent("");
  }

  useEffect(() => {
    load();
  }, [storyId]);

  return (
    <div className="card">
      <div className="section-title">
        <h3>Annotations</h3>
      </div>
      <textarea
        className="textarea"
        rows={3}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Add a comment or annotation..."
      />
      <button className="btn btn-secondary" onClick={add}>Add Annotation</button>
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {items.map((item) => (
          <div key={item.id} className="card-subtle">
            <div style={{ fontWeight: 600 }}>{item.annotation_type}</div>
            <div>{item.content}</div>
            <div className="pill">Votes: {item.votes_count}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
