import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { transactionsApi, type TransactionEditPayload, type TransactionFilters } from "./api";

export function useTransactions(filters: TransactionFilters) {
  return useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => transactionsApi.list(filters),
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: transactionsApi.categories,
    staleTime: Infinity, // categorias fixas do sistema — não mudam em runtime
  });
}

export function useCreateManualTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: transactionsApi.createManual,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: TransactionEditPayload }) =>
      transactionsApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => transactionsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}

export function useImportTransactions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: transactionsApi.importFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
  });
}
