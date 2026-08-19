import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { investmentsApi, type HoldingPayload } from "./api";

export function useInvestmentsTopMovers() {
  return useQuery({
    queryKey: ["investments-top-movers"],
    queryFn: investmentsApi.topMovers,
    staleTime: 5 * 60 * 1000, // acompanha o cache de 5min do backend
  });
}

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: investmentsApi.portfolio,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: HoldingPayload) => investmentsApi.createHolding(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useDeleteHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => investmentsApi.deleteHolding(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useBuyHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { quantity: string; price_cents: number } }) =>
      investmentsApi.buy(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}

export function useSellHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { quantity: string } }) =>
      investmentsApi.sell(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  });
}
