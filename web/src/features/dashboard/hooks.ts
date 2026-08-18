import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "./api";

export function useSummary(month: string) {
  return useQuery({
    queryKey: ["summary", month],
    queryFn: () => dashboardApi.summary(month),
  });
}
