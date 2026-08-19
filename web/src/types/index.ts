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

export interface InvestmentMover {
  symbol: string;
  name: string;
  price: number | null;
  change_pct: number;
  kind: "crypto" | "stock" | "fii";
}

export interface InvestmentsTopMovers {
  crypto: InvestmentMover[];
  stocks_and_fiis: InvestmentMover[];
}

export interface InsightsCategoryRow {
  category_slug: string;
  category_name: string;
  total_cents: number;
  pct_of_total: number;
  change_pct_vs_prev_month: number | null;
}

export interface InsightsCategoryChange {
  category_name: string;
  change_pct_vs_prev_month: number;
}

export interface InsightsBiggestTransaction {
  description: string;
  amount_cents: number;
  date: string;
  category_name: string;
}

export interface InsightsData {
  month: string;
  previous_month: string;
  total_expense_cents: number;
  total_expense_change_pct: number | null;
  daily_avg_expense_cents: number;
  top_categories: InsightsCategoryRow[];
  biggest_increase_category: InsightsCategoryChange | null;
  biggest_decrease_category: InsightsCategoryChange | null;
  biggest_single_transaction: InsightsBiggestTransaction | null;
  messages: string[];
}
