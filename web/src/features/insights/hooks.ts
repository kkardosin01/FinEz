import { useQuery } from "@tanstack/react-query";
import { insightsApi } from "./api";

export function useInsights(month: string) {
  return useQuery({
    queryKey: ["insights", month],
    queryFn: () => insightsApi.get(month),
  });
}
