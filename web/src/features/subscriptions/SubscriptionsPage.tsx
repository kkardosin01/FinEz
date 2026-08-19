import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { MoneyValue } from "@/components/ui/MoneyValue";
import { useCategories } from "@/features/transactions/hooks";
import type { Subscription } from "@/types";
import { useSubscriptions, useUpdateSubscription } from "./hooks";

const editSchema = z.object({
  name: z.string().min(1, "dê um nome pra assinatura"),
  category: z.coerce.number().optional(),
});
type EditFormData = z.infer<typeof editSchema>;

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR");
}

export function SubscriptionsPage() {
  const { data: subscriptions, isLoading } = useSubscriptions();
  const { data: categories } = useCategories();
  const updateSubscription = useUpdateSubscription();
  const [editingSubscription, setEditingSubscription] = useState<Subscription | null>(null);

  const editForm = useForm<EditFormData>({ resolver: zodResolver(editSchema) });

  const activeSubscriptions = subscriptions?.filter((s) => s.status === "active") ?? [];
  const monthlyTotalCents = activeSubscriptions.reduce((sum, s) => sum + s.amount_cents, 0);

  const openEdit = (subscription: Subscription) => {
    editForm.reset({ name: subscription.name, category: subscription.category ?? undefined });
    setEditingSubscription(subscription);
  };

  const onSubmitEdit = (data: EditFormData) => {
    if (!editingSubscription) return;
    updateSubscription.mutate(
      { id: editingSubscription.id, payload: { name: data.name, category: data.category ?? null } },
      { onSuccess: () => setEditingSubscription(null) }
    );
  };

  const toggleStatus = (subscription: Subscription) => {
    updateSubscription.mutate({
      id: subscription.id,
      payload: { status: subscription.status === "active" ? "canceled" : "active" },
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-semibold">Assinaturas</h1>
      </div>

      {!isLoading && activeSubscriptions.length > 0 && (
        <Card className="flex items-center justify-between">
          <span className="text-sm text-fg-secondary">Total por mês</span>
          <MoneyValue amountCents={-monthlyTotalCents} hideSign className="font-semibold" />
        </Card>
      )}

      {isLoading && <p className="text-sm text-fg-secondary">carregando...</p>}
      {!isLoading && subscriptions?.length === 0 && (
        <Card>
          <p className="text-sm text-fg-secondary">
            Nenhuma assinatura detectada ainda — assim que identificarmos gastos recorrentes
            (mensalidades, streamings etc.) eles aparecem aqui automaticamente.
          </p>
        </Card>
      )}

      <div className="space-y-3">
        {subscriptions?.map((subscription) => (
          <Card key={subscription.id} className={subscription.status === "canceled" ? "opacity-60" : ""}>
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium">{subscription.name}</p>
                <p className="text-xs text-fg-secondary">
                  {subscription.category_name ?? "sem categoria"} · última cobrança em{" "}
                  {formatDate(subscription.last_charged_at)}
                </p>
                {subscription.status === "canceled" && (
                  <p className="text-xs text-fg-secondary">cancelada — não monitoramos mais reajustes</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => openEdit(subscription)}
                className="p-2 text-fg-secondary hover:text-fg"
                aria-label="editar assinatura"
              >
                ✏️
              </button>
            </div>

            <div className="mt-2 flex items-center justify-between">
              <div>
                <MoneyValue amountCents={-subscription.amount_cents} hideSign className="font-mono font-semibold" />
                <span className="ml-1 text-xs text-fg-secondary">/mês</span>
                {subscription.previous_amount_cents !== null &&
                  subscription.previous_amount_cents !== subscription.amount_cents && (
                    <p className="text-xs text-warning">
                      {subscription.amount_cents > subscription.previous_amount_cents ? "📈 subiu de" : "📉 caiu de"}{" "}
                      <MoneyValue amountCents={-subscription.previous_amount_cents} hideSign />
                    </p>
                  )}
              </div>
              <Button size="sm" variant="secondary" onClick={() => toggleStatus(subscription)}>
                {subscription.status === "active" ? "cancelar" : "reativar"}
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Dialog
        open={!!editingSubscription}
        onOpenChange={(open) => !open && setEditingSubscription(null)}
        title="Editar assinatura"
      >
        <form onSubmit={editForm.handleSubmit(onSubmitEdit)} className="space-y-3">
          <input
            placeholder="nome"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...editForm.register("name")}
          />
          {editForm.formState.errors.name && (
            <p className="text-xs text-expense">{editForm.formState.errors.name.message}</p>
          )}

          <select
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...editForm.register("category")}
          >
            <option value="">sem categoria</option>
            {categories?.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name_pt}
              </option>
            ))}
          </select>

          <Button type="submit" className="w-full" disabled={updateSubscription.isPending}>
            {updateSubscription.isPending ? "salvando..." : "Salvar"}
          </Button>
        </form>
      </Dialog>
    </div>
  );
}
