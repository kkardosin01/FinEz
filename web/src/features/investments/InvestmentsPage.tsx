import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { MoneyValue } from "@/components/ui/MoneyValue";
import { cn } from "@/lib/utils";
import type { HoldingKind, PortfolioHolding } from "@/types";
import { InvestmentsSection } from "./InvestmentsSection";
import { useBuyHolding, useCreateHolding, useDeleteHolding, usePortfolio, useSellHolding } from "./hooks";

const KIND_LABEL: Record<HoldingKind, string> = { stock: "Ação", fii: "FII", crypto: "Cripto" };

const holdingSchema = z.object({
  kind: z.enum(["stock", "fii", "crypto"]),
  symbol: z.string().min(1, "informe o ticker (ações/FIIs) ou o id da CoinGecko (cripto)"),
  name: z.string().optional(),
  quantity: z.coerce.number().positive("quantidade deve ser maior que zero"),
  avg_price: z.coerce.number().positive("preço médio deve ser maior que zero"),
});
type HoldingFormData = z.infer<typeof holdingSchema>;

const buySchema = z.object({
  quantity: z.coerce.number().positive("quantidade deve ser maior que zero"),
  price: z.coerce.number().positive("preço deve ser maior que zero"),
});
type BuyFormData = z.infer<typeof buySchema>;

const sellSchema = z.object({
  quantity: z.coerce.number().positive("quantidade deve ser maior que zero"),
});
type SellFormData = z.infer<typeof sellSchema>;

export function InvestmentsPage() {
  const { data: portfolio, isLoading } = usePortfolio();
  const createHolding = useCreateHolding();
  const deleteHolding = useDeleteHolding();
  const buyHolding = useBuyHolding();
  const sellHolding = useSellHolding();

  const [createOpen, setCreateOpen] = useState(false);
  const [buyingHolding, setBuyingHolding] = useState<PortfolioHolding | null>(null);
  const [sellingHolding, setSellingHolding] = useState<PortfolioHolding | null>(null);
  const [deletingHolding, setDeletingHolding] = useState<PortfolioHolding | null>(null);

  const holdingForm = useForm<HoldingFormData>({ resolver: zodResolver(holdingSchema) });
  const buyForm = useForm<BuyFormData>({ resolver: zodResolver(buySchema) });
  const sellForm = useForm<SellFormData>({ resolver: zodResolver(sellSchema) });

  const openCreate = () => {
    holdingForm.reset({ kind: "stock", symbol: "", name: "", quantity: undefined, avg_price: undefined });
    setCreateOpen(true);
  };

  const onSubmitHolding = (data: HoldingFormData) => {
    createHolding.mutate(
      {
        kind: data.kind,
        symbol: data.symbol.trim().toUpperCase(),
        name: data.name,
        quantity: String(data.quantity),
        avg_price_cents: Math.round(data.avg_price * 100),
      },
      { onSuccess: () => setCreateOpen(false) }
    );
  };

  const openBuy = (holding: PortfolioHolding) => {
    buyForm.reset({ quantity: undefined, price: undefined });
    setBuyingHolding(holding);
  };

  const onSubmitBuy = (data: BuyFormData) => {
    if (!buyingHolding) return;
    buyHolding.mutate(
      { id: buyingHolding.id, payload: { quantity: String(data.quantity), price_cents: Math.round(data.price * 100) } },
      { onSuccess: () => setBuyingHolding(null) }
    );
  };

  const openSell = (holding: PortfolioHolding) => {
    sellForm.reset({ quantity: undefined });
    setSellingHolding(holding);
  };

  const onSubmitSell = (data: SellFormData) => {
    if (!sellingHolding) return;
    sellHolding.mutate(
      { id: sellingHolding.id, payload: { quantity: String(data.quantity) } },
      { onSuccess: () => setSellingHolding(null) }
    );
  };

  const handleDelete = () => {
    if (!deletingHolding) return;
    deleteHolding.mutate(deletingHolding.id, { onSuccess: () => setDeletingHolding(null) });
  };

  const holdings = portfolio?.holdings ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-semibold">Investimentos</h1>
        <Button size="sm" onClick={openCreate}>
          + Ativo
        </Button>
      </div>

      {!isLoading && holdings.length > 0 && (
        <Card className="grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-xs text-fg-secondary">Investido</p>
            <MoneyValue amountCents={portfolio!.total_invested_cents} hideSign className="text-sm font-semibold" />
          </div>
          <div>
            <p className="text-xs text-fg-secondary">Atual</p>
            {portfolio!.total_current_cents !== null ? (
              <MoneyValue amountCents={portfolio!.total_current_cents} hideSign className="text-sm font-semibold" />
            ) : (
              <p className="text-sm text-fg-secondary">—</p>
            )}
          </div>
          <div>
            <p className="text-xs text-fg-secondary">Ganho/perda</p>
            {portfolio!.total_gain_cents !== null ? (
              <p className={cn("text-sm font-semibold", portfolio!.total_gain_cents >= 0 ? "text-income" : "text-expense")}>
                {portfolio!.total_gain_cents >= 0 ? "+" : ""}
                {(portfolio!.total_gain_cents / 100).toFixed(2)}
              </p>
            ) : (
              <p className="text-sm text-fg-secondary">—</p>
            )}
          </div>
        </Card>
      )}

      {isLoading && <p className="text-sm text-fg-secondary">carregando...</p>}
      {!isLoading && holdings.length === 0 && (
        <Card>
          <p className="text-sm text-fg-secondary">
            Nenhum ativo na carteira ainda — toque em <em>+ Ativo</em> pra registrar uma ação, FII ou
            criptomoeda que você já tem.
          </p>
        </Card>
      )}

      <div className="space-y-3">
        {holdings.map((holding) => (
          <Card key={holding.id} className="space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium">
                  {holding.symbol} <span className="text-xs text-fg-secondary">{KIND_LABEL[holding.kind]}</span>
                </p>
                {holding.name && <p className="text-xs text-fg-secondary">{holding.name}</p>}
                <p className="text-xs text-fg-secondary">{holding.quantity} un.</p>
              </div>
              <button
                type="button"
                onClick={() => setDeletingHolding(holding)}
                className="p-2 text-fg-secondary hover:text-expense"
                aria-label="excluir ativo"
              >
                🗑️
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <MoneyValue amountCents={holding.invested_cents} hideSign className="font-mono font-semibold" />
                <p className="text-xs text-fg-secondary">investido</p>
              </div>
              {holding.current_value_cents !== null && holding.gain_pct !== null ? (
                <div className="text-right">
                  <MoneyValue amountCents={holding.current_value_cents} hideSign className="font-mono font-semibold" />
                  <p className={cn("text-xs", holding.gain_pct >= 0 ? "text-income" : "text-expense")}>
                    {holding.gain_pct >= 0 ? "+" : ""}
                    {holding.gain_pct.toFixed(2)}%
                  </p>
                </div>
              ) : (
                <p className="text-xs text-fg-secondary">cotação indisponível</p>
              )}
            </div>

            <div className="flex gap-2">
              <Button size="sm" variant="secondary" className="flex-1" onClick={() => openBuy(holding)}>
                Comprar mais
              </Button>
              <Button size="sm" variant="secondary" className="flex-1" onClick={() => openSell(holding)}>
                Vender
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <InvestmentsSection />

      <Dialog open={createOpen} onOpenChange={setCreateOpen} title="Novo ativo">
        <form onSubmit={holdingForm.handleSubmit(onSubmitHolding)} className="space-y-3">
          <select
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...holdingForm.register("kind")}
          >
            <option value="stock">Ação</option>
            <option value="fii">FII</option>
            <option value="crypto">Cripto</option>
          </select>

          <input
            placeholder="ticker (ex: PETR4) ou id CoinGecko (ex: bitcoin)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...holdingForm.register("symbol")}
          />
          {holdingForm.formState.errors.symbol && (
            <p className="text-xs text-expense">{holdingForm.formState.errors.symbol.message}</p>
          )}

          <input
            placeholder="nome (opcional)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
            {...holdingForm.register("name")}
          />

          <input
            type="number"
            step="any"
            placeholder="quantidade"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...holdingForm.register("quantity")}
          />
          {holdingForm.formState.errors.quantity && (
            <p className="text-xs text-expense">{holdingForm.formState.errors.quantity.message}</p>
          )}

          <input
            type="number"
            step="0.01"
            placeholder="preço médio de compra (R$)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...holdingForm.register("avg_price")}
          />
          {holdingForm.formState.errors.avg_price && (
            <p className="text-xs text-expense">{holdingForm.formState.errors.avg_price.message}</p>
          )}

          <Button type="submit" className="w-full" disabled={createHolding.isPending}>
            {createHolding.isPending ? "salvando..." : "Adicionar ativo"}
          </Button>
        </form>
      </Dialog>

      <Dialog
        open={!!buyingHolding}
        onOpenChange={(open) => !open && setBuyingHolding(null)}
        title={buyingHolding ? `Comprar mais ${buyingHolding.symbol}` : ""}
      >
        <form onSubmit={buyForm.handleSubmit(onSubmitBuy)} className="space-y-3">
          <input
            type="number"
            step="any"
            placeholder="quantidade comprada"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...buyForm.register("quantity")}
          />
          {buyForm.formState.errors.quantity && (
            <p className="text-xs text-expense">{buyForm.formState.errors.quantity.message}</p>
          )}
          <input
            type="number"
            step="0.01"
            placeholder="preço pago (R$, por unidade)"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...buyForm.register("price")}
          />
          {buyForm.formState.errors.price && (
            <p className="text-xs text-expense">{buyForm.formState.errors.price.message}</p>
          )}
          <Button type="submit" className="w-full" disabled={buyHolding.isPending}>
            {buyHolding.isPending ? "salvando..." : "Confirmar compra"}
          </Button>
        </form>
      </Dialog>

      <Dialog
        open={!!sellingHolding}
        onOpenChange={(open) => !open && setSellingHolding(null)}
        title={sellingHolding ? `Vender ${sellingHolding.symbol}` : ""}
      >
        <form onSubmit={sellForm.handleSubmit(onSubmitSell)} className="space-y-3">
          <p className="text-xs text-fg-secondary">você tem {sellingHolding?.quantity} un.</p>
          <input
            type="number"
            step="any"
            placeholder="quantidade vendida"
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] font-mono"
            {...sellForm.register("quantity")}
          />
          {sellForm.formState.errors.quantity && (
            <p className="text-xs text-expense">{sellForm.formState.errors.quantity.message}</p>
          )}
          <Button type="submit" className="w-full" disabled={sellHolding.isPending}>
            {sellHolding.isPending ? "salvando..." : "Confirmar venda"}
          </Button>
        </form>
      </Dialog>

      <Dialog
        open={!!deletingHolding}
        onOpenChange={(open) => !open && setDeletingHolding(null)}
        title="Excluir ativo"
      >
        <div className="space-y-3">
          <p className="text-sm text-fg-secondary">
            Isso remove <strong>{deletingHolding?.symbol}</strong> da sua carteira. Não dá pra desfazer.
          </p>
          <Button variant="danger" className="w-full" disabled={deleteHolding.isPending} onClick={handleDelete}>
            {deleteHolding.isPending ? "excluindo..." : "Excluir ativo"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
