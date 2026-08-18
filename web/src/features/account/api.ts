import { api } from "@/lib/api";
import type { Theme } from "@/types";

export interface PairingStatus {
  pairing_code?: string;
  expires_at?: string;
  status: "unlinked" | "pending" | "active";
  phone_e164?: string | null;
}

export const accountApi = {
  updateTheme: (theme: Theme) => api.patch("/me", { theme }),
  pairingStatus: () => api.get<PairingStatus>("/whatsapp/pair"),
  generatePairingCode: () => api.post<PairingStatus>("/whatsapp/pair"),
};
