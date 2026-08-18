import { api } from "@/lib/api";
import type { Connection } from "@/types";

export const connectionsApi = {
  list: () => api.get<Connection[]>("/connections"),
  createConnectToken: (itemId?: string) =>
    api.post<{ connect_token: string }>("/connections", itemId ? { item_id: itemId } : undefined),
  revoke: (id: string) => api.delete<void>(`/connections/${id}`),
};
