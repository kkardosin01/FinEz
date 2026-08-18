import { api } from "@/lib/api";
import type { Budget } from "@/types";

export interface BudgetUpsertPayload {
  month: string;
  budgets: { category: number; amount_cents: number }[];
}

export const budgetsApi = {
  list: (month: string) => api.get<Budget[]>(`/budgets?month=${month}`),
  upsert: (payload: BudgetUpsertPayload) => api.put<Budget[]>("/budgets", payload),
};
