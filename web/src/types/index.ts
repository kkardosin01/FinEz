// Tipos manuais alinhados ao schema OpenAPI do backend (drf-spectacular).
// TODO: substituir por geração automática (`openapi-typescript`) assim que o
// backend estiver rodando — ver seção 3 "Decisões de arquitetura".

export type Theme = "light" | "dark" | "system";

export interface Me {
  id: string;
  email: string;
  name: string | null;
  theme: Theme;
  birth_date: string | null;
  date_joined: string;
}

export interface Category {
  id: number;
  slug: string;
  name_pt: string;
  color_light: string;
  color_dark: string;
}

export type CategorySource = "provider" | "rule" | "llm" | "user";
export type TransactionOrigin = "bank" | "whatsapp" | "web";

export interface Transaction {
  id: string;
  account: string;
  account_name: string;
  amount_cents: number;
  description: string;
  date: string;
  category: number;
  category_slug: string;
  category_source: CategorySource;
  origin: TransactionOrigin;
  created_at: string;
}

export interface Budget {
  id: string;
  category: number;
  category_slug: string;
  category_name: string;
  amount_cents: number;
  month: string;
  spent_cents: number;
}

export interface Connection {
  id: string;
  provider: string;
  institution_name: string;
  institution_logo: string;
  status: "syncing" | "active" | "error" | "revoked";
  last_synced_at: string | null;
  created_at: string;
}

export interface SummaryCategoryRow {
  category_slug: string;
  category_name: string;
  color_light: string;
  color_dark: string;
  total_cents: number;
}

export interface Summary {
  month: string;
  income_cents: number;
  expense_cents: number;
  balance_cents: number;
  by_category: SummaryCategoryRow[];
  daily: { date: string; total_cents: number }[];
}
