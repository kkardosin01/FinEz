import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useCategories, useCreateManualTransaction } from "./hooks";

const schema = z.object({
  description: z.string().min(1, "descreva o lançamento"),
  amount: z.coerce.number().positive("valor deve ser maior que zero"),
  type: z.enum(["income", "expense"]),
  date: z.string().min(1),
  category: z.coerce.number().min(1, "escolha uma categoria"),
});
type FormData = z.infer<typeof schema>;

export function ManualTransactionDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { data: categories } = useCategories();
  const createTransaction = useCreateManualTransaction();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { type: "expense", date: new Date().toISOString().slice(0, 10) },
  });

  const onSubmit = (data: FormData) => {
    const amountCents = Math.round(data.amount * 100);
    createTransaction.mutate(
      {
        description: data.description,
        date: data.date,
        category: data.category,
        amount_cents: data.type === "expense" ? -amountCents : amountCents,
      },
      {
        onSuccess: () => {
          reset();
          onOpenChange(false);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Novo lançamento">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <div className="flex gap-2">
          <label className="flex-1 flex items-center gap-2 rounded-lg border border-border px-3 py-2 min-h-[44px]">
            <input type="radio" value="expense" {...register("type")} defaultChecked />
            Gasto
          </label>
          <label className="flex-1 flex items-center gap-2 rounded-lg border border-border px-3 py-2 min-h-[44px]">
            <input type="radio" value="income" {...register("type")} />
            Entrada
          </label>
        </div>

        <input
          placeholder="descrição (ex.: lanche na padaria)"
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

        <Button type="submit" className="w-full" disabled={createTransaction.isPending}>
          {createTransaction.isPending ? "salvando..." : "Salvar lançamento"}
        </Button>
      </form>
    </Dialog>
  );
}
