import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { connectionsApi } from "./api";

export function useConnections() {
  return useQuery({
    queryKey: ["connections"],
    queryFn: connectionsApi.list,
  });
}

export function useCreateConnectToken() {
  return useMutation({
    mutationFn: (itemId?: string) => connectionsApi.createConnectToken(itemId),
  });
}

export function useRevokeConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => connectionsApi.revoke(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["connections"] }),
  });
}
