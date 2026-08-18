import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { BudgetBar } from "@/components/ui/BudgetBar";
import { Card } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { PeriodNav } from "@/components/ui/PeriodNav";
import { useMonthParam } from "@/hooks/useMonthParam";
import { useCategories } from "@/features/transactions/hooks";
import { useBudgets, useUpsertBudget } from "./hooks";

const schema = z.object({
  category: z.coerce.number().min(1, "escolha uma categoria"),
  amount: z.coerce.number().positive("valor deve ser maior que zero"),
});
type FormData = z.infer<typeof schema>;

export function BudgetsPage() {
  const { month, next, previous } = useMonthParam();
  const { data: budgets, isLoading } = useBudgets(month);
  const { data: categories } = useCategories();
  const upsertBudget = useUpsertBudget();
  const [dialogOpen, setDialogOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormData) => {
    upsertBudget.mutate(
      {
        month: `${month}-01`,
        budgets: [{ category: data.category, amount_cents: Math.round(data.amount * 100) }],
      },
      { onSuccess: () => { reset(); setDialogOpen(false); } }
    );
  };

  const budgetedCategoryIds = new Set(budgets?.map((b) => b.category));
  const availableCategories = categories?.filter((cat) => !budgetedCategoryIds.has(cat.id));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-semibold">Orçamentos</h1>
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          + Definir limite
        </Button>
      </div>

      <PeriodNav month={month} onPrevious={previous} onNext={next} />

      <Card className="divide-y divide-border p-0">
        {isLoading && <p className="p-4 text-sm text-fg-secondary">carregando...</p>}
        {!isLoading && budgets?.length === 0 && (
          <p className="p-4 text-sm text-fg-secondary">
            Nenhum limite definido pra este mês — toque em <em>+ Definir limite</em> pra começar
          </p>
        )}
        <div className="px-4">
          {budgets?.map((budget) => (
            <div key={budget.id} className="py-3">
              <BudgetBar
                categoryName={budget.category_name}
                spentCents={budget.spent_cents}
                limitCents={budget.amount_cents}
              />
            </div>
          ))}
        </div>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen} title="Definir limite">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <select className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("category")}>
            <option value="">categoria</option>
            {availableCategories?.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name_pt}
              </option>
            ))}
          </select>
          {errors.category && <p className="text-xs text-expense">{errors.category.message}</p>}

          <input
            type="number"
            step="0.01"
            placeholder="limite mensal (R$)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...register("amount")}
          />
          {errors.amount && <p className="text-xs text-expense">{errors.amount.message}</p>}

          <Button type="submit" className="w-full" disabled={upsertBudget.isPending}>
            {upsertBudget.isPending ? "salvando..." : "Salvar limite"}
          </Button>
        </form>
      </Dialog>
    </div>
  );
}
