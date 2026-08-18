import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { transactionsApi, type TransactionFilters } from "./api";

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

export function useRecategorize() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, category }: { id: string; category: number }) =>
      transactionsApi.recategorize(id, category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
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
