import { api } from "@/lib/api";
import type { InvestmentsTopMovers } from "@/types";

export const investmentsApi = {
  topMovers: () => api.get<InvestmentsTopMovers>("/investments/top-movers"),
};
