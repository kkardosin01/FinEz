import { api } from "@/lib/api";
import type { EngagementSummary } from "@/types";

export const engagementApi = {
  summary: () => api.get<EngagementSummary>("/engagement/summary"),
};
