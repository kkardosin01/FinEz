import { Card } from "@/components/ui/Card";
import type { InvestmentMover } from "@/types";
import { useInvestmentsTopMovers } from "./hooks";

const KIND_LABEL: Record<InvestmentMover["kind"], string> = {
  crypto: "cripto",
  stock: "ação",
  fii: "FII",
};

export function InvestmentsSection() {
  const { data, isLoading } = useInvestmentsTopMovers();
  const crypto = data?.crypto ?? [];
  const stocksAndFiis = data?.stocks_and_fiis ?? [];
  const hasData = crypto.length > 0 || stocksAndFiis.length > 0;

  return (
    <Card className="space-y-3">
      <h3 className="font-heading font-semibold">Maiores altas do dia</h3>
      {isLoading && <p className="text-sm text-fg-secondary">carregando...</p>}
      {!isLoading && !hasData && (
        <p className="text-sm text-fg-secondary">
          Não foi possível buscar cotações agora — tenta de novo em instantes.
        </p>
      )}
      {!isLoading && hasData && (
        <div className="grid gap-4 sm:grid-cols-2">
          <MoverGroup title="Ações e FIIs" movers={stocksAndFiis} />
          <MoverGroup title="Criptomoedas" movers={crypto} />
        </div>
      )}
    </Card>
  );
}

function MoverGroup({ title, movers }: { title: string; movers: InvestmentMover[] }) {
  if (movers.length === 0) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-fg-secondary">{title}</p>
      <ul className="space-y-1.5">
        {movers.map((mover) => (
          <li key={mover.symbol} className="flex items-center justify-between gap-2 text-sm">
            <span className="min-w-0 truncate">
              <span className="font-medium">{mover.symbol}</span>{" "}
              <span className="text-xs text-fg-secondary">{KIND_LABEL[mover.kind]}</span>
            </span>
            <span className="shrink-0 font-medium text-income">
              +{mover.change_pct.toFixed(2)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
