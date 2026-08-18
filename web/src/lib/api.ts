// API client único (seção 3): nenhum componente chama `fetch` direto.
// Sessão via cookie httpOnly — sempre `credentials: "include"` + header CSRF.

const API_URL = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method || "GET";
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  const isFormData = options.body instanceof FormData;
  if (options.body && !isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    throw new ApiError(response.status, body);
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: data ? JSON.stringify(data) : undefined }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PUT", body: data ? JSON.stringify(data) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export { API_URL };
