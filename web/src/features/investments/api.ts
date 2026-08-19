import { api } from "@/lib/api";
import type { Holding, InvestmentsTopMovers, PortfolioSummary } from "@/types";

export interface HoldingPayload {
  kind: Holding["kind"];
  symbol: string;
  name?: string;
  quantity: string;
  avg_price_cents: number;
}

export const investmentsApi = {
  topMovers: () => api.get<InvestmentsTopMovers>("/investments/top-movers"),
  portfolio: () => api.get<PortfolioSummary>("/investments/portfolio"),
  createHolding: (payload: HoldingPayload) => api.post<Holding>("/investments/holdings", payload),
  deleteHolding: (id: string) => api.delete<void>(`/investments/holdings/${id}`),
  buy: (id: string, payload: { quantity: string; price_cents: number }) =>
    api.post<Holding>(`/investments/holdings/${id}/buy`, payload),
  sell: (id: string, payload: { quantity: string }) =>
    api.post<Holding | undefined>(`/investments/holdings/${id}/sell`, payload),
};
