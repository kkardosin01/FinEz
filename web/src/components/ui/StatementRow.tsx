import type { Transaction } from "@/types";
import { formatDateShort } from "@/lib/format";
import { MoneyValue } from "./MoneyValue";
import { cn } from "@/lib/utils";

interface StatementRowProps {
  transaction: Transaction;
  onClick?: () => void;
}

const ORIGIN_LABEL: Record<Transaction["origin"], string> = {
  bank: "banco",
  whatsapp: "whatsapp",
  web: "manual",
};

export function StatementRow({ transaction, onClick }: StatementRowProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center justify-between gap-3 py-3 text-left min-h-[44px] border-b border-border last:border-0"
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{transaction.description}</p>
        <p className="text-xs text-fg-secondary">
          {formatDateShort(transaction.date)} · {transaction.category_slug} ·{" "}
          {ORIGIN_LABEL[transaction.origin]}
        </p>
      </div>
      <MoneyValue
        amountCents={transaction.amount_cents}
        className={cn("shrink-0 text-sm font-medium")}
      />
    </button>
  );
}
