import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/api";
import { authApi, type LoginPayload, type RegisterPayload } from "./api";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    retry: false,
    // 401 é esperado quando deslogado — não é um erro de rede
    throwOnError: (error) => !(error instanceof ApiError && error.status === 401),
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
