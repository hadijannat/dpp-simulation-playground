import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../services/api";

export function useProgress() {
  const progress = useQuery({
    queryKey: ["progress"],
    queryFn: () => apiGet("/api/v1/progress"),
  });

  const epics = useQuery({
    queryKey: ["progress-epics"],
    queryFn: () => apiGet("/api/v1/progress/epics"),
  });

  return { progress, epics };
}
