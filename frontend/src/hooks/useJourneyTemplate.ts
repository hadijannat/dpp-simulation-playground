import { useQuery } from "@tanstack/react-query";
import { getJourneyTemplates, getJourneyTemplate } from "../services/platformV2Service";

export function useJourneyTemplates() {
  return useQuery({
    queryKey: ["journey-templates"],
    queryFn: getJourneyTemplates,
  });
}

export function useJourneyTemplate(code: string | undefined) {
  return useQuery({
    queryKey: ["journey-template", code],
    queryFn: () => getJourneyTemplate(code!),
    enabled: !!code,
  });
}
