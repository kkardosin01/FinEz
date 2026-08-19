import { useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card } from "@/components/ui/Card";
import { MoneyValue } from "@/components/ui/MoneyValue";
import { PeriodNav } from "@/components/ui/PeriodNav";
import { useThemeStore } from "@/app/theme-store";
import { useMonthParam } from "@/hooks/useMonthParam";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { ConnectionsSection } from "@/features/connections/ConnectionsPage";
import { EngagementSection } from "@/features/engagement/EngagementSection";
import { InvestmentsSection } from "@/features/investments/InvestmentsSection";
import type { TransactionFilters } from "@/features/transactions/api";
import { TransactionsSection } from "@/features/transactions/TransactionsSection";
import { useSummary } from "./hooks";

type TxFilter = Pick<TransactionFilters, "category" | "type" | "day" | "search">;

export function DashboardPage() {
  const { month, previous, next } = useMonthParam();
  const { data: summary, isLoading } = useSummary(month);
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme);
  const reducedMotion = usePrefersReducedMotion();
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [txFilter, setTxFilter] = useState<TxFilter>({});

  const applyFilter = (patch: Partial<TxFilter>) => setTxFilter((prev) => ({ ...prev, ...patch }));

  if (isLoading || !summary) {
    return <p className="text-fg-secondary">carregando...</p>;
  }

  const expenseRows = summary.by_category.filter((row) => row.total_cents < 0);
  const totalExpenseCents = expenseRows.reduce((sum, row) => sum + Math.abs(row.total_cents), 0);
  const donutData = expenseRows.map((row) => ({
    name: row.category_name,
    slug: row.category_slug,
    value: Math.abs(row.total_cents),
    color: resolvedTheme === "dark" ? row.color_dark : row.color_light,
  }));

  const toggleCategory = (slug: string) => {
    if (activeCategory === slug) {
      setActiveCategory(null);
      applyFilter({ category: undefined });
    } else {
      setActiveCategory(slug);
      applyFilter({ category: slug, type: undefined, day: undefined });
    }
  };

  return (
    <div className="space-y-6">
      <PeriodNav month={month} onPrevious={previous} onNext={next} />

      <div className="grid grid-cols-3 gap-3">
        <SummaryCard
          label="Entradas"
          cents={summary.income_cents}
          onClick={() => {
            setActiveCategory(null);
            applyFilter({ type: "income", category: undefined, day: undefined });
          }}
        />
        <SummaryCard
          label="Saídas"
          cents={summary.expense_cents}
          onClick={() => {
            setActiveCategory(null);
            applyFilter({ type: "expense", category: undefined, day: undefined });
          }}
        />
        <SummaryCard
          label="Balanço"
          cents={summary.balance_cents}
          onClick={() => {
            setActiveCategory(null);
            applyFilter({ type: undefined, category: undefined, day: undefined });
          }}
        />
      </div>

      <EngagementSection />

      <ConnectionsSection />

      <Card>
        <h3 className="mb-3 font-heading font-semibold">Gastos por categoria</h3>
        {donutData.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="h-56 md:w-1/2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={donutData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="55%"
                    outerRadius="80%"
                    isAnimationActive={!reducedMotion}
                    onClick={(entry) => toggleCategory((entry as unknown as { slug: string }).slug)}
                  >
                    {donutData.map((entry) => (
                      <Cell key={entry.slug} fill={entry.color} cursor="pointer" />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => `R$ ${(value / 100).toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="flex-1 space-y-2">
              {donutData
                .slice()
                .sort((a, b) => b.value - a.value)
                .map((row) => {
                  const pct = totalExpenseCents ? (row.value / totalExpenseCents) * 100 : 0;
                  return (
                    <li key={row.slug}>
                      <button
                        type="button"
                        onClick={() => toggleCategory(row.slug)}
                        className={`flex w-full items-center justify-between gap-2 rounded-lg px-2 py-2 min-h-[44px] text-left ${
                          activeCategory === row.slug ? "bg-income/10" : "hover:bg-bg"
                        }`}
                      >
                        <span className="flex items-center gap-2 min-w-0">
                          <span
                            className="h-2.5 w-2.5 shrink-0 rounded-full"
                            style={{ backgroundColor: row.color }}
                            aria-hidden
                          />
                          <span className="truncate text-sm font-medium">{row.name}</span>
                        </span>
                        <span className="flex shrink-0 items-center gap-2">
                          <span className="text-xs text-fg-secondary">{pct.toFixed(0)}%</span>
                          <MoneyValue amountCents={-row.value} className="text-sm" hideSign />
                        </span>
                      </button>
                    </li>
                  );
                })}
            </ul>
          </div>
        )}
      </Card>

      <Card>
        <TransactionsSection
          title="Transações"
          filters={{ month, ...txFilter }}
          onFilterChange={applyFilter}
        />
      </Card>

      <InvestmentsSection />
    </div>
  );
}

function SummaryCard({ label, cents, onClick }: { label: string; cents: number; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="text-left">
      <Card className="min-h-[44px] space-y-1">
        <p className="text-xs text-fg-secondary">{label}</p>
        <MoneyValue amountCents={cents} className="text-sm font-semibold" hideSign />
      </Card>
    </button>
  );
}

function EmptyState() {
  return (
    <p className="py-8 text-center text-sm text-fg-secondary">
      Manda um <em>oi</em> pro bot ou conecta seu banco — seu extrato aparece aqui
    </p>
  );
}
