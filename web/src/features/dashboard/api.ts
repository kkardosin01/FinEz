import { api } from "@/lib/api";
import type { Summary } from "@/types";

export const dashboardApi = {
  summary: (month: string) => api.get<Summary>(`/summary?month=${month}`),
};
