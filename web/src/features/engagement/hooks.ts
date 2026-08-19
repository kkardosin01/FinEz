import { useQuery } from "@tanstack/react-query";
import { engagementApi } from "./api";

export function useEngagementSummary() {
  return useQuery({
    queryKey: ["engagement-summary"],
    queryFn: () => engagementApi.summary(),
  });
}
