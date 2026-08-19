import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  goalsApi,
  type ContributePayload,
  type GoalCreatePayload,
  type GoalUpdatePayload,
} from "./api";

export function useGoals() {
  return useQuery({
    queryKey: ["goals"],
    queryFn: () => goalsApi.list(),
  });
}

export function useCreateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GoalCreatePayload) => goalsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useUpdateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: GoalUpdatePayload }) => goalsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useDeleteGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => goalsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useContribute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ContributePayload }) => goalsApi.contribute(id, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["goal-contributions", variables.id] });
    },
  });
}

export function useGoalContributions(id: string, enabled: boolean) {
  return useQuery({
    queryKey: ["goal-contributions", id],
    queryFn: () => goalsApi.contributions(id),
    enabled,
  });
}
