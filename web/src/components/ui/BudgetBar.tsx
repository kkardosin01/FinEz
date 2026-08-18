import { MoneyValue } from "./MoneyValue";
import { cn } from "@/lib/utils";

interface BudgetBarProps {
  categoryName: string;
  spentCents: number;
  limitCents: number;
  onClick?: () => void;
}

/** Barra de orçamento — tocar expande as transações que consumiram o limite. */
export function BudgetBar({ categoryName, spentCents, limitCents, onClick }: BudgetBarProps) {
  const ratio = limitCents > 0 ? spentCents / limitCents : 0;
  const percent = Math.min(ratio, 1) * 100;
  const isOver = ratio >= 1;
  const isWarning = ratio >= 0.8 && !isOver;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left space-y-1.5 min-h-[44px] py-1"
    >
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{categoryName}</span>
        <span className="text-fg-secondary">
          <MoneyValue amountCents={spentCents} hideSign className="text-fg" /> de{" "}
          <MoneyValue amountCents={limitCents} hideSign className="text-fg-secondary" />
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-bg overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-[width]",
            isOver ? "bg-expense" : isWarning ? "bg-warning" : "bg-income"
          )}
          style={{ width: `${percent}%` }}
        />
      </div>
      {isOver && (
        <p className="text-xs text-expense">
          estourou em <MoneyValue amountCents={spentCents - limitCents} hideSign />
        </p>
      )}
    </button>
  );
}
