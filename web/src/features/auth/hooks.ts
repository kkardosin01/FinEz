import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/api";
import { authApi, type LoginPayload, type RegisterPayload } from "./api";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    retry: false,
    // 401/403 são esperados quando deslogado (DRF SessionAuthentication retorna
    // 403, não 401, pois não emite desafio WWW-Authenticate) — não é erro de rede
    throwOnError: (error) =>
      !(error instanceof ApiError && (error.status === 401 || error.status === 403)),
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LoginPayload) => authApi.login(payload),
    onSuccess: (me) => queryClient.setQueryData(["me"], me),
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authApi.register(payload),
    onSuccess: (me) => queryClient.setQueryData(["me"], me),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => queryClient.setQueryData(["me"], null),
  });
}
