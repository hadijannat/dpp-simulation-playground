import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../services/api";
import type { EpicProgressResponse, ProgressResponse } from "../types/api.types";

export function useProgress() {
  const progress = useQuery({
    queryKey: ["progress"],
    queryFn: () => apiGet<ProgressResponse>("/api/v2/simulation/progress"),
  });

  const epics = useQuery({
    queryKey: ["progress-epics"],
    queryFn: () => apiGet<EpicProgressResponse>("/api/v2/simulation/progress/epics"),
  });

  return { progress, epics };
}
