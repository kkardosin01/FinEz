import { useSearchParams } from "react-router-dom";
import type { TransactionFilters } from "./api";
import { TransactionsSection } from "./TransactionsSection";

const PARAM_MAP: Record<keyof Omit<TransactionFilters, "month">, string> = {
  category: "categoria",
  type: "tipo",
  day: "dia",
  search: "busca",
};

/** Página dedicada — mantida pra links diretos/compartilháveis; a navegação
 * principal usa a seção de transações embutida na Visão geral. */
export function TransactionsPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters: TransactionFilters = {
    month: searchParams.get("mes") ?? undefined,
    category: searchParams.get("categoria") ?? undefined,
    type: (searchParams.get("tipo") as "income" | "expense" | null) ?? undefined,
    day: searchParams.get("dia") ?? undefined,
    search: searchParams.get("busca") ?? undefined,
  };

  const handleFilterChange = (patch: Partial<TransactionFilters>) => {
    const next = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(patch)) {
      const param = key === "month" ? "mes" : PARAM_MAP[key as keyof typeof PARAM_MAP];
      if (value) next.set(param, String(value));
      else next.delete(param);
    }
    setSearchParams(next);
  };

  return <TransactionsSection filters={filters} onFilterChange={handleFilterChange} />;
}
