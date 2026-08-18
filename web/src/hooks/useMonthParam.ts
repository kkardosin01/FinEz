import { useSearchParams } from "react-router-dom";

function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

/** Filtros como URL (seção 3): compartilhável, sobrevive a refresh, botão voltar funciona. */
export function useMonthParam() {
  const [searchParams, setSearchParams] = useSearchParams();
  const month = searchParams.get("mes") || currentMonth();

  const setMonth = (value: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("mes", value);
    setSearchParams(next);
  };

  const shift = (delta: number) => {
    const [year, monthNum] = month.split("-").map(Number);
    const date = new Date(year, monthNum - 1 + delta, 1);
    setMonth(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`);
  };

  return { month, setMonth, next: () => shift(1), previous: () => shift(-1) };
}
