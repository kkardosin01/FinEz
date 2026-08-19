import { api } from "@/lib/api";
import type { Subscription, SubscriptionStatus } from "@/types";

export interface SubscriptionUpdatePayload {
  name?: string;
  category?: number | null;
  status?: SubscriptionStatus;
}

export const subscriptionsApi = {
  list: () => api.get<Subscription[]>("/subscriptions"),
  update: (id: string, payload: SubscriptionUpdatePayload) => api.patch<Subscription>(`/subscriptions/${id}`, payload),
};
