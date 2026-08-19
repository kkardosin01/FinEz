import { useQuery } from "@tanstack/react-query";
import { investmentsApi } from "./api";

export function useInvestmentsTopMovers() {
  return useQuery({
    queryKey: ["investments-top-movers"],
    queryFn: investmentsApi.topMovers,
    staleTime: 5 * 60 * 1000, // acompanha o cache de 5min do backend
  });
}
