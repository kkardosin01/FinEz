import { formatMonthLabel } from "@/lib/format";

interface PeriodNavProps {
  month: string;
  onPrevious: () => void;
  onNext: () => void;
}

/** Período navegável: ‹ › pra trocar de mês em qualquer painel (seção 2). */
export function PeriodNav({ month, onPrevious, onNext }: PeriodNavProps) {
  return (
    <div className="flex items-center justify-between">
      <button
        type="button"
        onClick={onPrevious}
        aria-label="mês anterior"
        className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-card"
      >
        ‹
      </button>
      <h2 className="font-heading text-lg font-semibold">{formatMonthLabel(month)}</h2>
      <button
        type="button"
        onClick={onNext}
        aria-label="próximo mês"
        className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-card"
      >
        ›
      </button>
    </div>
  );
}
