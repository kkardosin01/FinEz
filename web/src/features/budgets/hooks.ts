import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { budgetsApi, type BudgetUpsertPayload } from "./api";

export function useBudgets(month: string) {
  return useQuery({
    queryKey: ["budgets", month],
    queryFn: () => budgetsApi.list(month),
  });
}

export function useUpsertBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: BudgetUpsertPayload) => budgetsApi.upsert(payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["budgets", variables.month.slice(0, 7)] });
    },
  });
}
