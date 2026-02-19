import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../../services/api";
import type { components } from "../../types/generated/platform-api";

type AnnotationItem = components["schemas"]["AnnotationItem"];
type GapItem = components["schemas"]["GapItem"];
type VoteItem = components["schemas"]["VoteItem"];

type CommentItem = {
  id: string;
  target_id: string;
  content: string;
  created_at?: string | null;
};

type AnnotationListResponse = { items: AnnotationItem[] };
type GapListResponse = { items: GapItem[] };
type CommentListResponse = { items: CommentItem[] };

type GapLane = "open" | "in_progress" | "resolved";

const LANE_LABELS: Record<GapLane, string> = {
  open: "Open",
  in_progress: "In Progress",
  resolved: "Resolved",
};

function normalizeGapStatus(value: string | null | undefined): GapLane {
  const normalized = String(value || "open").toLowerCase().replace("-", "_");
  if (normalized === "resolved") return "resolved";
  if (normalized === "in_progress" || normalized === "inprogress") return "in_progress";
  return "open";
}

function formatDate(value?: string | null): string {
  if (!value) return "n/a";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

export default function CollaborationBoard({ storyId }: { storyId?: number }) {
  const queryClient = useQueryClient();
  const [annotationContent, setAnnotationContent] = useState("");
  const [gapDescription, setGapDescription] = useState("");
  const [commentDrafts, setCommentDrafts] = useState<Record<string, string>>({});

  const annotations = useQuery({
    queryKey: ["collaboration-board", "annotations", storyId || "all"],
    queryFn: () =>
      apiGet<AnnotationListResponse>(
        `/api/v2/collaboration/annotations?${new URLSearchParams({
          limit: "100",
          ...(storyId ? { story_id: String(storyId) } : {}),
        }).toString()}`,
      ),
    refetchInterval: 10000,
  });

  const gaps = useQuery({
    queryKey: ["collaboration-board", "gaps", storyId || "all"],
    queryFn: () =>
      apiGet<GapListResponse>(
        `/api/v2/collaboration/gaps?${new URLSearchParams({
          limit: "100",
          ...(storyId ? { story_id: String(storyId) } : {}),
        }).toString()}`,
      ),
    refetchInterval: 10000,
  });

  const comments = useQuery({
    queryKey: ["collaboration-board", "comments"],
    queryFn: () => apiGet<CommentListResponse>("/api/v2/collaboration/comments?limit=200"),
    refetchInterval: 10000,
  });

  const addAnnotation = useMutation({
    mutationFn: (content: string) =>
      apiPost<AnnotationItem>("/api/v2/collaboration/annotations", {
        story_id: storyId,
        annotation_type: "comment",
        content,
      }),
    onSuccess: () => {
      setAnnotationContent("");
      queryClient.invalidateQueries({ queryKey: ["collaboration-board", "annotations"] });
    },
  });

  const addGap = useMutation({
    mutationFn: (description: string) =>
      apiPost<GapItem>("/api/v2/collaboration/gaps", {
        story_id: storyId,
        description,
      }),
    onSuccess: () => {
      setGapDescription("");
      queryClient.invalidateQueries({ queryKey: ["collaboration-board", "gaps"] });
    },
  });

  const addComment = useMutation({
    mutationFn: ({ targetId, content }: { targetId: string; content: string }) =>
      apiPost<CommentItem>("/api/v2/collaboration/comments", {
        target_id: targetId,
        content,
      }),
    onSuccess: (_data, variables) => {
      setCommentDrafts((current) => ({ ...current, [variables.targetId]: "" }));
      queryClient.invalidateQueries({ queryKey: ["collaboration-board", "comments"] });
    },
  });

  const vote = useMutation({
    mutationFn: ({ targetId, value }: { targetId: string; value: 1 | -1 }) =>
      apiPost<VoteItem>("/api/v2/collaboration/votes", { target_id: targetId, value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collaboration-board", "annotations"] });
      queryClient.invalidateQueries({ queryKey: ["collaboration-board", "gaps"] });
    },
  });

  const gapItems = gaps.data?.items || [];
  const annotationItems = annotations.data?.items || [];
  const commentItems = comments.data?.items || [];

  const commentsByTarget = useMemo(() => {
    const grouped = new Map<string, CommentItem[]>();
    commentItems.forEach((item) => {
      const bucket = grouped.get(item.target_id) || [];
      bucket.push(item);
      grouped.set(item.target_id, bucket);
    });
    return grouped;
  }, [commentItems]);

  const gapsByLane = useMemo(() => {
    const grouped: Record<GapLane, GapItem[]> = {
      open: [],
      in_progress: [],
      resolved: [],
    };
    gapItems.forEach((gap) => {
      grouped[normalizeGapStatus(gap.status)].push(gap);
    });
    return grouped;
  }, [gapItems]);

  function submitAnnotation() {
    const value = annotationContent.trim();
    if (!value) return;
    addAnnotation.mutate(value);
  }

  function submitGap() {
    const value = gapDescription.trim();
    if (!value) return;
    addGap.mutate(value);
  }

  function submitComment(targetId: string) {
    const value = (commentDrafts[targetId] || "").trim();
    if (!value) return;
    addComment.mutate({ targetId, content: value });
  }

  function renderCommentThread(targetId: string) {
    const thread = commentsByTarget.get(targetId) || [];
    return (
      <div className="collaboration-comments">
        <div style={{ fontWeight: 600 }}>Comments ({thread.length})</div>
        {thread.length > 0 ? (
          <div style={{ display: "grid", gap: 6 }}>
            {thread.map((item) => (
              <div key={item.id} className="collaboration-comment-item">
                <div>{item.content}</div>
                <small style={{ color: "var(--ink-muted)" }}>{formatDate(item.created_at)}</small>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: "var(--ink-muted)" }}>No comments yet.</div>
        )}
        <div style={{ display: "flex", gap: 8 }}>
          <input
            className="input"
            placeholder="Add a comment..."
            value={commentDrafts[targetId] || ""}
            onChange={(event) => setCommentDrafts((current) => ({ ...current, [targetId]: event.target.value }))}
          />
          <button className="btn btn-secondary" onClick={() => submitComment(targetId)}>
            Comment
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="collaboration-board-grid">
      <div className="card-subtle">
        <h3>Add Annotation</h3>
        <textarea
          className="textarea"
          rows={3}
          value={annotationContent}
          onChange={(event) => setAnnotationContent(event.target.value)}
          placeholder="Highlight context, evidence, or feedback..."
        />
        <button className="btn btn-secondary" onClick={submitAnnotation}>
          Add Annotation
        </button>
      </div>

      <div className="card-subtle">
        <h3>Report Gap</h3>
        <textarea
          className="textarea"
          rows={3}
          value={gapDescription}
          onChange={(event) => setGapDescription(event.target.value)}
          placeholder="Describe a missing requirement or inconsistency..."
        />
        <button className="btn btn-primary" onClick={submitGap}>
          Submit Gap
        </button>
      </div>

      <div className="collaboration-lanes">
        {(Object.keys(LANE_LABELS) as GapLane[]).map((lane) => (
          <div key={lane} className="card collaboration-lane">
            <div className="section-title">
              <h3>{LANE_LABELS[lane]}</h3>
              <span className="pill">{gapsByLane[lane].length}</span>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              {gapsByLane[lane].map((gap) => (
                <div key={gap.id} className="collaboration-card">
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <strong>Gap #{gap.id}</strong>
                    <span className="pill">{gap.status || "open"}</span>
                  </div>
                  <div>{gap.description}</div>
                  <div style={{ color: "var(--ink-muted)" }}>{formatDate(gap.created_at)}</div>
                  <div className="collaboration-actions">
                    <span className="pill">Votes: {gap.votes_count || 0}</span>
                    <button className="btn btn-secondary" onClick={() => vote.mutate({ targetId: gap.id, value: 1 })}>Upvote</button>
                    <button className="btn btn-secondary" onClick={() => vote.mutate({ targetId: gap.id, value: -1 })}>Downvote</button>
                  </div>
                  {renderCommentThread(gap.id)}
                </div>
              ))}
              {gapsByLane[lane].length === 0 && <div style={{ color: "var(--ink-muted)" }}>No gaps in this lane.</div>}
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="section-title">
          <h3>Annotations</h3>
          <span className="pill">{annotationItems.length}</span>
        </div>
        {annotations.isLoading && <div>Loading annotations...</div>}
        {annotations.error && <div className="error">Failed to load annotations.</div>}
        <div style={{ display: "grid", gap: 10 }}>
          {annotationItems.map((item) => (
            <div key={item.id} className="collaboration-card">
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <strong>{item.annotation_type || "comment"}</strong>
                <span className="pill">{item.status || "open"}</span>
              </div>
              <div>{item.content}</div>
              <div style={{ color: "var(--ink-muted)" }}>{formatDate(item.created_at)}</div>
              <div className="collaboration-actions">
                <span className="pill">Votes: {item.votes_count || 0}</span>
                <button className="btn btn-secondary" onClick={() => vote.mutate({ targetId: item.id, value: 1 })}>Upvote</button>
                <button className="btn btn-secondary" onClick={() => vote.mutate({ targetId: item.id, value: -1 })}>Downvote</button>
              </div>
              {renderCommentThread(item.id)}
            </div>
          ))}
          {annotationItems.length === 0 && !annotations.isLoading && (
            <div style={{ color: "var(--ink-muted)" }}>No annotations yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
