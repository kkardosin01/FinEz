import { api } from "@/lib/api";
import type { Category, Transaction } from "@/types";

export interface TransactionFilters {
  month?: string;
  category?: string;
  type?: "income" | "expense";
  day?: string;
  search?: string;
}

function toQueryString(filters: TransactionFilters): string {
  const params = new URLSearchParams();
  if (filters.month) params.set("month", filters.month);
  if (filters.category) params.set("category", filters.category);
  if (filters.type) params.set("type", filters.type);
  if (filters.day) params.set("day", filters.day);
  if (filters.search) params.set("search", filters.search);
  return params.toString();
}

export interface PaginatedTransactions {
  count: number;
  results: Transaction[];
}

export interface ImportResult {
  imported: number;
  errors: string[];
}

export interface TransactionEditPayload {
  description: string;
  date: string;
  category: number;
  amount_cents: number;
}

export const transactionsApi = {
  list: (filters: TransactionFilters) =>
    api.get<PaginatedTransactions>(`/transactions?${toQueryString(filters)}`),
  update: (id: string, payload: TransactionEditPayload) =>
    api.patch<Transaction>(`/transactions/${id}`, payload),
  remove: (id: string) => api.delete<void>(`/transactions/${id}`),
  createManual: (payload: { amount_cents: number; description: string; date: string; category: number }) =>
    api.post<Transaction>("/transactions", payload),
  categories: () => api.get<Category[]>("/categories"),
  importFile: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.postForm<ImportResult>("/imports/transactions", formData);
  },
};
