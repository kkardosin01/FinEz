import { Card } from "@/components/ui/Card";
import { MoneyValue } from "@/components/ui/MoneyValue";
import { PeriodNav } from "@/components/ui/PeriodNav";
import { formatDateShort } from "@/lib/format";
import { useMonthParam } from "@/hooks/useMonthParam";
import type { InsightsCategoryRow } from "@/types";
import { useInsights } from "./hooks";

export function InsightsPage() {
  const { month, previous, next } = useMonthParam();
  const { data, isLoading } = useInsights(month);

  return (
    <div className="space-y-6">
      <PeriodNav month={month} onPrevious={previous} onNext={next} />

      {isLoading || !data ? (
        <p className="text-fg-secondary">carregando...</p>
      ) : (
        <>
          <HighlightsCard messages={data.messages} />
          <ComparisonCard
            totalExpenseCents={data.total_expense_cents}
            changePct={data.total_expense_change_pct}
            dailyAvgExpenseCents={data.daily_avg_expense_cents}
          />
          <TopCategoriesCard categories={data.top_categories} />
          {data.biggest_single_transaction && (
            <Card className="space-y-1">
              <h3 className="font-heading font-semibold">Maior gasto individual</h3>
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{data.biggest_single_transaction.description}</p>
                  <p className="text-xs text-fg-secondary">
                    {data.biggest_single_transaction.category_name} ·{" "}
                    {formatDateShort(data.biggest_single_transaction.date)}
                  </p>
                </div>
                <MoneyValue amountCents={data.biggest_single_transaction.amount_cents} className="shrink-0 text-sm" />
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function HighlightsCard({ messages }: { messages: string[] }) {
  return (
    <Card className="space-y-2">
      <h3 className="font-heading font-semibold">Destaques do mês</h3>
      <ul className="space-y-1.5">
        {messages.map((message) => (
          <li key={message} className="text-sm">
            {message}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function ComparisonCard({
  totalExpenseCents,
  changePct,
  dailyAvgExpenseCents,
}: {
  totalExpenseCents: number;
  changePct: number | null;
  dailyAvgExpenseCents: number;
}) {
  return (
    <Card className="space-y-3">
      <h3 className="font-heading font-semibold">Comparação com o mês passado</h3>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-fg-secondary">Total gasto</p>
          <MoneyValue amountCents={totalExpenseCents} className="text-lg font-semibold" hideSign />
        </div>
        {changePct !== null && (
          <span className={`text-sm font-medium ${changePct > 0 ? "text-expense" : "text-income"}`}>
            {changePct > 0 ? "↑" : "↓"} {Math.abs(changePct).toFixed(0)}%
          </span>
        )}
      </div>
      <p className="text-xs text-fg-secondary">
        Média diária: <MoneyValue amountCents={dailyAvgExpenseCents} className="text-xs" hideSign />
      </p>
    </Card>
  );
}

function TopCategoriesCard({ categories }: { categories: InsightsCategoryRow[] }) {
  return (
    <Card className="space-y-2">
      <h3 className="font-heading font-semibold">Maiores gastos por categoria</h3>
      {categories.length === 0 ? (
        <p className="text-sm text-fg-secondary">Nenhum gasto registrado nesse mês ainda.</p>
      ) : (
        <ul className="space-y-2">
          {categories.map((row) => (
            <li key={row.category_slug} className="flex items-center justify-between gap-2">
              <span className="min-w-0 truncate text-sm font-medium">{row.category_name}</span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="text-xs text-fg-secondary">{row.pct_of_total.toFixed(0)}%</span>
                {row.change_pct_vs_prev_month !== null && (
                  <span
                    className={`text-xs font-medium ${
                      row.change_pct_vs_prev_month > 0 ? "text-expense" : "text-income"
                    }`}
                  >
                    {row.change_pct_vs_prev_month > 0 ? "↑" : "↓"} {Math.abs(row.change_pct_vs_prev_month).toFixed(0)}%
                  </span>
                )}
                <MoneyValue amountCents={row.total_cents} className="text-sm" hideSign />
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
