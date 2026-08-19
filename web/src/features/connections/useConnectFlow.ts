import { useState } from "react";
import { api } from "@/lib/api";
import { useCreateConnectToken } from "./hooks";

// Widget oficial do Pluggy Connect (carregado via CDN só quando necessário).
// NOTA: confirme a versão/URL atual no painel do Pluggy antes de ir pra produção —
// aqui assumimos o pacote hospedado deles pra evitar bundlar credenciais no front.
const PLUGGY_CONNECT_SCRIPT_URL = "https://cdn.pluggy.ai/pluggy-connect/v2.9.0/pluggy-connect.js";

declare global {
  interface Window {
    PluggyConnect?: new (opts: {
      connectToken: string;
      onSuccess: (data: { item: { id: string } }) => void;
      onError?: (error: unknown) => void;
      onClose?: () => void;
    }) => { init: () => void };
  }
}

function loadPluggyScript(): Promise<void> {
  if (window.PluggyConnect) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = PLUGGY_CONNECT_SCRIPT_URL;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("widget indisponível"));
    document.body.appendChild(script);
  });
}

/** Fluxo de abrir o widget do Pluggy Connect — reaproveitado na página de
 * conexões e no popup pós-cadastro. */
export function useConnectFlow(onSuccess?: () => void) {
  const createConnectToken = useCreateConnectToken();
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = async () => {
    setError(null);
    setConnecting(true);
    try {
      const { connect_token } = await createConnectToken.mutateAsync(undefined);
      await loadPluggyScript();
      const widget = new window.PluggyConnect!({
        connectToken: connect_token,
        onSuccess: async (data) => {
          await api.post("/connections/callback", { item_id: data.item.id });
          onSuccess ? onSuccess() : window.location.reload();
        },
        onError: () => setError("não foi possível conectar — tenta de novo em instantes"),
      });
      widget.init();
    } catch {
      setError("widget do banco indisponível neste ambiente — credenciais do Pluggy ainda não configuradas");
    } finally {
      setConnecting(false);
    }
  };

  return { connect, connecting, error };
}
