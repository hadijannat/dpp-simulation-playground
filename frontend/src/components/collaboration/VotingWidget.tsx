import { apiPost } from "../../services/api";

export default function VotingWidget({ targetId }: { targetId: string }) {
  async function vote(value: number) {
    await apiPost("/api/v1/votes", { target_id: targetId, value });
  }

  return (
    <div style={{ display: "flex", gap: 6 }}>
      <button className="btn btn-secondary" onClick={() => vote(1)}>Upvote</button>
      <button className="btn btn-secondary" onClick={() => vote(-1)}>Downvote</button>
    </div>
  );
}
