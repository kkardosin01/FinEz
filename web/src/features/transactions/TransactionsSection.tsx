import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CategoryChip } from "@/components/ui/CategoryChip";
import { StatementRow } from "@/components/ui/StatementRow";
import type { Transaction } from "@/types";
import type { TransactionFilters } from "./api";
import { ImportTransactionsDialog } from "./ImportTransactionsDialog";
import { ManualTransactionDialog } from "./ManualTransactionDialog";
import { useCategories, useRecategorize, useTransactions } from "./hooks";

interface TransactionsSectionProps {
  filters: TransactionFilters;
  onFilterChange: (patch: Partial<TransactionFilters>) => void;
  title?: string;
}

/**
 * Conteúdo de transações extraído pra ser reaproveitado tanto na página
 * dedicada (/transacoes, acesso via link direto) quanto embutido na Visão geral.
 */
export function TransactionsSection({ filters, onFilterChange, title = "Transações" }: TransactionsSectionProps) {
  const { data: categories } = useCategories();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [editing, setEditing] = useState<Transaction | null>(null);
  const recategorize = useRecategorize();
  const { data, isLoading } = useTransactions(filters);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-heading font-semibold">{title}</h3>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => setImportOpen(true)}>
            Importar
          </Button>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            + Lançar
          </Button>
        </div>
      </div>

      <input
        placeholder="buscar na descrição..."
        defaultValue={filters.search}
        onChange={(e) => onFilterChange({ search: e.target.value || undefined })}
        className="w-full rounded-lg border border-border bg-card px-3 py-2 min-h-[44px]"
      />

      <div className="flex flex-wrap gap-2">
        {categories?.map((cat) => (
          <CategoryChip
            key={cat.id}
            name={cat.name_pt}
            colorLight={cat.color_light}
            colorDark={cat.color_dark}
            active={filters.category === cat.slug}
            onClick={() =>
              onFilterChange({ category: filters.category === cat.slug ? undefined : cat.slug })
            }
          />
        ))}
      </div>

      <Card className="divide-y divide-border p-0">
        {isLoading && <p className="p-4 text-sm text-fg-secondary">carregando...</p>}
        {!isLoading && data?.results.length === 0 && (
          <p className="p-4 text-sm text-fg-secondary">
            Manda um <em>oi</em> pro bot ou conecta seu banco — seu extrato aparece aqui
          </p>
        )}
        <div className="px-4">
          {data?.results.map((tx) => (
            <StatementRow key={tx.id} transaction={tx} onClick={() => setEditing(tx)} />
          ))}
        </div>
      </Card>

      <ManualTransactionDialog open={dialogOpen} onOpenChange={setDialogOpen} />
      <ImportTransactionsDialog open={importOpen} onOpenChange={setImportOpen} />

      {editing && (
        <RecategorizeSheet
          transaction={editing}
          onClose={() => setEditing(null)}
          onSelect={(categoryId) =>
            recategorize.mutate(
              { id: editing.id, category: categoryId },
              { onSuccess: () => setEditing(null) }
            )
          }
        />
      )}
    </div>
  );
}

function RecategorizeSheet({
  transaction,
  onClose,
  onSelect,
}: {
  transaction: Transaction;
  onClose: () => void;
  onSelect: (categoryId: number) => void;
}) {
  const { data: categories } = useCategories();

  return (
    <div className="fixed inset-0 z-20 flex items-end bg-black/40" onClick={onClose}>
      <div
        className="w-full rounded-t-card bg-card p-4 space-y-3"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-heading font-semibold">{transaction.description}</h3>
        <p className="text-sm text-fg-secondary">escolha a categoria certa</p>
        <div className="flex flex-wrap gap-2">
          {categories?.map((cat) => (
            <CategoryChip
              key={cat.id}
              name={cat.name_pt}
              colorLight={cat.color_light}
              colorDark={cat.color_dark}
              active={transaction.category === cat.id}
              onClick={() => onSelect(cat.id)}
            />
          ))}
        </div>
        <Button variant="secondary" className="w-full" onClick={onClose}>
          cancelar
        </Button>
      </div>
    </div>
  );
}
