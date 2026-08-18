import { formatCents } from "@/lib/format";
import { cn } from "@/lib/utils";

interface MoneyValueProps {
  /** Centavos, sempre integer. Dinheiro nunca trafega como float (seção 3). */
  amountCents: number;
  className?: string;
  /** Esconde o sinal +/- (usado em contextos onde o sinal já é redundante) */
  hideSign?: boolean;
}

/**
 * Componente único que renderiza todo valor monetário do app.
 * Entradas em verde com "+", saídas em vermelho com "−" — sempre sinal + cor
 * juntos (acessibilidade pra daltonismo).
 */
export function MoneyValue({ amountCents, className, hideSign = false }: MoneyValueProps) {
  const isNegative = amountCents < 0;
  const sign = hideSign ? "" : isNegative ? "− " : "+ ";

  return (
    <span
      className={cn(
        "font-mono tabular-nums",
        isNegative ? "text-expense" : "text-income",
        className
      )}
    >
      {sign}R$ {formatCents(amountCents)}
    </span>
  );
}
