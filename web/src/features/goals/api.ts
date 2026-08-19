import { api } from "@/lib/api";
import type { GoalContribution, SavingsGoal } from "@/types";

export interface GoalCreatePayload {
  name: string;
  icon?: string;
  target_cents: number;
  target_date?: string | null;
}

export interface GoalUpdatePayload {
  name?: string;
  icon?: string;
  target_cents?: number;
  target_date?: string | null;
}

export interface ContributePayload {
  amount_cents: number;
  note?: string;
}

export const goalsApi = {
  list: () => api.get<SavingsGoal[]>("/goals"),
  create: (payload: GoalCreatePayload) => api.post<SavingsGoal>("/goals", payload),
  update: (id: string, payload: GoalUpdatePayload) => api.patch<SavingsGoal>(`/goals/${id}`, payload),
  remove: (id: string) => api.delete(`/goals/${id}`),
  contribute: (id: string, payload: ContributePayload) =>
    api.post<SavingsGoal>(`/goals/${id}/contribute`, payload),
  contributions: (id: string) => api.get<GoalContribution[]>(`/goals/${id}/contributions`),
};
