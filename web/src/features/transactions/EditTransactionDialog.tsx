import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import type { Transaction } from "@/types";
import { useCategories, useDeleteTransaction, useUpdateTransaction } from "./hooks";

// Categorias que representam dinheiro entrando na conta — nunca podem ser um gasto
const INCOME_ONLY_SLUGS = new Set(["income", "extra_income"]);

const schema = z.object({
  description: z.string().min(1, "descreva o lançamento"),
  amount: z.coerce.number().positive("valor deve ser maior que zero"),
  type: z.enum(["income", "expense"]),
  date: z.string().min(1),
  category: z.coerce.number().min(1, "escolha uma categoria"),
});
type FormData = z.infer<typeof schema>;

export function EditTransactionDialog({ transaction, onClose }: { transaction: Transaction; onClose: () => void }) {
  const { data: categories } = useCategories();
  const updateTransaction = useUpdateTransaction();
  const deleteTransaction = useDeleteTransaction();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      description: transaction.description,
      amount: Math.abs(transaction.amount_cents) / 100,
      type: transaction.amount_cents < 0 ? "expense" : "income",
      date: transaction.date,
      category: transaction.category,
    },
  });

  const selectedCategoryId = watch("category");
  const selectedCategory = categories?.find((cat) => cat.id === Number(selectedCategoryId));
  const isIncomeOnlyCategory = selectedCategory ? INCOME_ONLY_SLUGS.has(selectedCategory.slug) : false;

  useEffect(() => {
    if (isIncomeOnlyCategory) {
      setValue("type", "income");
    }
  }, [isIncomeOnlyCategory, setValue]);

  const onSubmit = (data: FormData) => {
    const amountCents = Math.round(data.amount * 100);
    updateTransaction.mutate(
      {
        id: transaction.id,
        payload: {
          description: data.description,
          date: data.date,
          category: data.category,
          amount_cents: data.type === "expense" ? -amountCents : amountCents,
        },
      },
      { onSuccess: onClose }
    );
  };

  const onDelete = () => {
    deleteTransaction.mutate(transaction.id, { onSuccess: onClose });
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()} title="Editar lançamento">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <div className="flex gap-2">
          <label
            className={`flex-1 flex items-center gap-2 rounded-lg border border-border px-3 py-2 min-h-[44px] ${
              isIncomeOnlyCategory ? "opacity-50" : ""
            }`}
          >
            <input type="radio" value="expense" {...register("type")} disabled={isIncomeOnlyCategory} />
            Gasto
          </label>
          <label className="flex-1 flex items-center gap-2 rounded-lg border border-border px-3 py-2 min-h-[44px]">
            <input type="radio" value="income" {...register("type")} />
            Entrada
          </label>
        </div>
        {isIncomeOnlyCategory && (
          <p className="text-xs text-fg-secondary">salário e renda extra são sempre dinheiro entrando na conta</p>
        )}

        <input
          placeholder="descrição"
          className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
          {...register("description")}
        />
        {errors.description && <p className="text-xs text-expense">{errors.description.message}</p>}

        <input
          type="number"
          step="0.01"
          placeholder="valor (R$)"
          className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
          {...register("amount")}
        />
        {errors.amount && <p className="text-xs text-expense">{errors.amount.message}</p>}

        <input type="date" className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("date")} />

        <select className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("category")}>
          <option value="">categoria</option>
          {categories?.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name_pt}
            </option>
          ))}
        </select>
        {errors.category && <p className="text-xs text-expense">{errors.category.message}</p>}

        <Button type="submit" className="w-full" disabled={updateTransaction.isPending}>
          {updateTransaction.isPending ? "salvando..." : "Salvar alterações"}
        </Button>

        {!confirmingDelete ? (
          <Button type="button" variant="ghost" className="w-full text-expense" onClick={() => setConfirmingDelete(true)}>
            Apagar lançamento
          </Button>
        ) : (
          <div className="space-y-2 rounded-lg border border-expense/40 p-3">
            <p className="text-sm">Tem certeza? Essa ação não pode ser desfeita.</p>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" className="flex-1" onClick={() => setConfirmingDelete(false)}>
                cancelar
              </Button>
              <Button type="button" variant="danger" className="flex-1" onClick={onDelete} disabled={deleteTransaction.isPending}>
                {deleteTransaction.isPending ? "apagando..." : "apagar"}
              </Button>
            </div>
          </div>
        )}
      </form>
    </Dialog>
  );
}
