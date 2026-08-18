import { api } from "@/lib/api";
import type { Me } from "@/types";

export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
  birth_date?: string;
  invite_code: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  me: () => api.get<Me>("/me"),
  register: (payload: RegisterPayload) => api.post<Me>("/auth/register", payload),
  login: (payload: LoginPayload) => api.post<Me>("/auth/login", payload),
  logout: () => api.post<void>("/auth/logout"),
};
