import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { subscriptionsApi, type SubscriptionUpdatePayload } from "./api";

export function useSubscriptions() {
  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => subscriptionsApi.list(),
  });
}

export function useUpdateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SubscriptionUpdatePayload }) =>
      subscriptionsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["subscriptions"] }),
  });
}
