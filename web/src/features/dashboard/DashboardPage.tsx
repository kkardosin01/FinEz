import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Area, AreaChart, XAxis } from "recharts";
import { Card } from "@/components/ui/Card";
import { MoneyValue } from "@/components/ui/MoneyValue";
import { PeriodNav } from "@/components/ui/PeriodNav";
import { useThemeStore } from "@/app/theme-store";
import { useMonthParam } from "@/hooks/useMonthParam";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { formatDateShort } from "@/lib/format";
import { useSummary } from "./hooks";

export function DashboardPage() {
  const { month, previous, next } = useMonthParam();
  const { data: summary, isLoading } = useSummary(month);
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme);
  const reducedMotion = usePrefersReducedMotion();
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  if (isLoading || !summary) {
    return <p className="text-fg-secondary">carregando...</p>;
  }

  const donutData = summary.by_category
    .filter((row) => row.total_cents < 0)
    .map((row) => ({
      name: row.category_name,
      slug: row.category_slug,
      value: Math.abs(row.total_cents),
      color: resolvedTheme === "dark" ? row.color_dark : row.color_light,
    }));

  const goToTransactions = (params: Record<string, string>) => {
    const search = new URLSearchParams({ mes: month, ...params });
    navigate(`/transacoes?${search.toString()}`);
  };

  return (
    <div className="space-y-6">
      <PeriodNav month={month} onPrevious={previous} onNext={next} />

      <div className="grid grid-cols-3 gap-3">
        <SummaryCard label="Entradas" cents={summary.income_cents} onClick={() => goToTransactions({ tipo: "income" })} />
        <SummaryCard label="Saídas" cents={summary.expense_cents} onClick={() => goToTransactions({ tipo: "expense" })} />
        <SummaryCard label="Balanço" cents={summary.balance_cents} onClick={() => goToTransactions({})} />
      </div>

      <Card>
        <h3 className="mb-3 font-heading font-semibold">Gastos por categoria</h3>
        {donutData.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius="55%"
                  outerRadius="80%"
                  isAnimationActive={!reducedMotion}
                  onClick={(entry) => {
                    const slug = (entry as unknown as { slug: string }).slug;
                    if (activeCategory === slug) {
                      setActiveCategory(null);
                    } else {
                      setActiveCategory(slug);
                      goToTransactions({ categoria: slug });
                    }
                  }}
                >
                  {donutData.map((entry) => (
                    <Cell key={entry.slug} fill={entry.color} cursor="pointer" />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `R$ ${(value / 100).toFixed(2)}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <Card>
        <h3 className="mb-3 font-heading font-semibold">Evolução do mês</h3>
        {summary.daily.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={summary.daily}
                onClick={(state) => {
                  const label = state?.activeLabel as string | undefined;
                  if (label) goToTransactions({ dia: label });
                }}
              >
                <XAxis dataKey="date" tickFormatter={formatDateShort} fontSize={11} />
                <Tooltip
                  labelFormatter={(label) => formatDateShort(label as string)}
                  formatter={(value: number) => `R$ ${(value / 100).toFixed(2)}`}
                />
                <Area
                  type="monotone"
                  dataKey="total_cents"
                  stroke="rgb(var(--color-income))"
                  fill="rgb(var(--color-income))"
                  fillOpacity={0.15}
                  isAnimationActive={!reducedMotion}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
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
