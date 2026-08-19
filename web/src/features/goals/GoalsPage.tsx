import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { MoneyValue } from "@/components/ui/MoneyValue";
import { cn } from "@/lib/utils";
import type { SavingsGoal } from "@/types";
import { useContribute, useCreateGoal, useDeleteGoal, useGoals, useUpdateGoal } from "./hooks";

const goalSchema = z.object({
  name: z.string().min(1, "dê um nome pra meta"),
  icon: z.string().max(8).optional(),
  target: z.coerce.number().positive("valor deve ser maior que zero"),
  target_date: z.string().optional(),
});
type GoalFormData = z.infer<typeof goalSchema>;

const contributeSchema = z.object({
  amount: z.coerce.number().refine((v) => v !== 0, "valor não pode ser zero"),
  note: z.string().optional(),
});
type ContributeFormData = z.infer<typeof contributeSchema>;

function GoalProgress({ goal }: { goal: SavingsGoal }) {
  return (
    <div className="space-y-1.5">
      <div className="h-2 w-full rounded-full bg-bg overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-[width]", goal.completed_at ? "bg-income" : "bg-income/70")}
          style={{ width: `${goal.progress_pct}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-sm text-fg-secondary">
        <MoneyValue amountCents={goal.saved_cents} hideSign className="text-fg" />
        <span>
          de <MoneyValue amountCents={goal.target_cents} hideSign className="text-fg-secondary" />
        </span>
      </div>
    </div>
  );
}

export function GoalsPage() {
  const { data: goals, isLoading } = useGoals();
  const createGoal = useCreateGoal();
  const updateGoal = useUpdateGoal();
  const deleteGoal = useDeleteGoal();
  const contribute = useContribute();

  const [createOpen, setCreateOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<SavingsGoal | null>(null);
  const [contributingGoal, setContributingGoal] = useState<SavingsGoal | null>(null);
  const [deletingGoal, setDeletingGoal] = useState<SavingsGoal | null>(null);

  const goalForm = useForm<GoalFormData>({ resolver: zodResolver(goalSchema) });
  const contributeForm = useForm<ContributeFormData>({ resolver: zodResolver(contributeSchema) });

  const openCreate = () => {
    goalForm.reset({ name: "", icon: "🐷", target: undefined, target_date: "" });
    setEditingGoal(null);
    setCreateOpen(true);
  };

  const openEdit = (goal: SavingsGoal) => {
    goalForm.reset({
      name: goal.name,
      icon: goal.icon,
      target: goal.target_cents / 100,
      target_date: goal.target_date ?? "",
    });
    setEditingGoal(goal);
    setCreateOpen(true);
  };

  const onSubmitGoal = (data: GoalFormData) => {
    const payload = {
      name: data.name,
      icon: data.icon || "🐷",
      target_cents: Math.round(data.target * 100),
      target_date: data.target_date || null,
    };
    if (editingGoal) {
      updateGoal.mutate({ id: editingGoal.id, payload }, { onSuccess: () => setCreateOpen(false) });
    } else {
      createGoal.mutate(payload, { onSuccess: () => setCreateOpen(false) });
    }
  };

  const openContribute = (goal: SavingsGoal) => {
    contributeForm.reset({ amount: undefined, note: "" });
    setContributingGoal(goal);
  };

  const onSubmitContribute = (data: ContributeFormData) => {
    if (!contributingGoal) return;
    contribute.mutate(
      { id: contributingGoal.id, payload: { amount_cents: Math.round(data.amount * 100), note: data.note } },
      { onSuccess: () => setContributingGoal(null) }
    );
  };

  const handleDelete = () => {
    if (!deletingGoal) return;
    deleteGoal.mutate(deletingGoal.id, { onSuccess: () => setDeletingGoal(null) });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-semibold">Metas de economia</h1>
        <Button size="sm" onClick={openCreate}>
          + Nova meta
        </Button>
      </div>

      {isLoading && <p className="text-sm text-fg-secondary">carregando...</p>}
      {!isLoading && goals?.length === 0 && (
        <Card>
          <p className="text-sm text-fg-secondary">
            Nenhuma meta ainda — toque em <em>+ Nova meta</em> pra começar a guardar dinheiro pra
            algo que você quer.
          </p>
        </Card>
      )}

      <div className="space-y-3">
        {goals?.map((goal) => (
          <Card key={goal.id} className="space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl" aria-hidden>
                  {goal.icon}
                </span>
                <div>
                  <p className="font-medium">{goal.name}</p>
                  {goal.completed_at && <p className="text-xs text-income">🎉 meta concluída</p>}
                  {!goal.completed_at && goal.target_date && (
                    <p className="text-xs text-fg-secondary">
                      até {new Date(`${goal.target_date}T00:00:00`).toLocaleDateString("pt-BR")}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => openEdit(goal)}
                  className="p-2 text-fg-secondary hover:text-fg"
                  aria-label="editar meta"
                >
                  ✏️
                </button>
                <button
                  type="button"
                  onClick={() => setDeletingGoal(goal)}
                  className="p-2 text-fg-secondary hover:text-expense"
                  aria-label="excluir meta"
                >
                  🗑️
                </button>
              </div>
            </div>

            <GoalProgress goal={goal} />

            <Button size="sm" variant="secondary" className="w-full" onClick={() => openContribute(goal)}>
              Guardar ou resgatar
            </Button>
          </Card>
        ))}
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen} title={editingGoal ? "Editar meta" : "Nova meta"}>
        <form onSubmit={goalForm.handleSubmit(onSubmitGoal)} className="space-y-3">
          <input
            placeholder="nome da meta (ex: viagem, tênis novo)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...goalForm.register("name")}
          />
          {goalForm.formState.errors.name && (
            <p className="text-xs text-expense">{goalForm.formState.errors.name.message}</p>
          )}

          <input
            placeholder="ícone (emoji, opcional)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...goalForm.register("icon")}
          />

          <input
            type="number"
            step="0.01"
            placeholder="valor da meta (R$)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...goalForm.register("target")}
          />
          {goalForm.formState.errors.target && (
            <p className="text-xs text-expense">{goalForm.formState.errors.target.message}</p>
          )}

          <input
            type="date"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...goalForm.register("target_date")}
          />

          <Button type="submit" className="w-full" disabled={createGoal.isPending || updateGoal.isPending}>
            {createGoal.isPending || updateGoal.isPending ? "salvando..." : "Salvar meta"}
          </Button>
        </form>
      </Dialog>

      <Dialog
        open={!!contributingGoal}
        onOpenChange={(open) => !open && setContributingGoal(null)}
        title={contributingGoal ? `${contributingGoal.icon} ${contributingGoal.name}` : ""}
      >
        <form onSubmit={contributeForm.handleSubmit(onSubmitContribute)} className="space-y-3">
          <p className="text-xs text-fg-secondary">
            valor positivo guarda dinheiro na meta, negativo resgata (ex: -50 pra tirar R$ 50)
          </p>
          <input
            type="number"
            step="0.01"
            placeholder="valor (R$)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...contributeForm.register("amount")}
          />
          {contributeForm.formState.errors.amount && (
            <p className="text-xs text-expense">{contributeForm.formState.errors.amount.message}</p>
          )}
          <input
            placeholder="nota (opcional)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...contributeForm.register("note")}
          />
          <Button type="submit" className="w-full" disabled={contribute.isPending}>
            {contribute.isPending ? "salvando..." : "Confirmar"}
          </Button>
        </form>
      </Dialog>

      <Dialog open={!!deletingGoal} onOpenChange={(open) => !open && setDeletingGoal(null)} title="Excluir meta">
        <div className="space-y-3">
          <p className="text-sm text-fg-secondary">
            Isso apaga a meta <strong>{deletingGoal?.name}</strong> e seu histórico de aportes. Não
            dá pra desfazer.
          </p>
          <Button variant="danger" className="w-full" disabled={deleteGoal.isPending} onClick={handleDelete}>
            {deleteGoal.isPending ? "excluindo..." : "Excluir meta"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
