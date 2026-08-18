import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Theme } from "@/types";
import { accountApi } from "./api";

export function usePairingStatus() {
  return useQuery({
    queryKey: ["whatsapp-pairing"],
    queryFn: accountApi.pairingStatus,
  });
}

export function useGeneratePairingCode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: accountApi.generatePairingCode,
    onSuccess: (data) => queryClient.setQueryData(["whatsapp-pairing"], data),
  });
}

export function useUpdateTheme() {
  return useMutation({
    mutationFn: (theme: Theme) => accountApi.updateTheme(theme),
  });
}
