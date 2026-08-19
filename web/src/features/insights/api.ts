import { api } from "@/lib/api";
import type { InsightsData } from "@/types";

export const insightsApi = {
  get: (month: string) => api.get<InsightsData>(`/insights?month=${month}`),
};
