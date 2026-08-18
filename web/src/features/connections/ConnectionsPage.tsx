import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { useConnections, useCreateConnectToken, useRevokeConnection } from "./hooks";

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

const STATUS_LABEL: Record<string, string> = {
  syncing: "sincronizando...",
  active: "ativa",
  error: "erro na sincronização",
  revoked: "revogada",
};

export function ConnectionsSection() {
  const { data: connections } = useConnections();
  const createConnectToken = useCreateConnectToken();
  const revoke = useRevokeConnection();
  const [connecting, setConnecting] = useState(false);
  const [widgetError, setWidgetError] = useState<string | null>(null);

  const handleConnect = async () => {
    setWidgetError(null);
    setConnecting(true);
    try {
      const { connect_token } = await createConnectToken.mutateAsync(undefined);
      await loadPluggyScript();
      const widget = new window.PluggyConnect!({
        connectToken: connect_token,
        onSuccess: async (data) => {
          await api.post("/connections/callback", { item_id: data.item.id });
          window.location.reload();
        },
        onError: () => setWidgetError("não foi possível conectar — tenta de novo em instantes"),
      });
      widget.init();
    } catch {
      setWidgetError(
        "widget do banco indisponível neste ambiente — credenciais do Pluggy ainda não configuradas"
      );
    } finally {
      setConnecting(false);
    }
  };

  return (
    <Card className="space-y-3">
      <h2 className="font-heading font-semibold">Bancos conectados</h2>
      {connections?.length === 0 && (
        <p className="text-sm text-fg-secondary">
          Conecte seu banco pra os gastos do cartão entrarem sozinhos.
        </p>
      )}
      <div className="space-y-2">
        {connections?.map((conn) => (
          <div key={conn.id} className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2 min-h-[44px]">
            <div>
              <p className="text-sm font-medium">{conn.institution_name || "instituição"}</p>
              <p className="text-xs text-fg-secondary">{STATUS_LABEL[conn.status] ?? conn.status}</p>
            </div>
            {conn.status !== "revoked" && (
              <Button size="sm" variant="secondary" onClick={() => revoke.mutate(conn.id)} disabled={revoke.isPending}>
                desconectar
              </Button>
            )}
          </div>
        ))}
      </div>
      {widgetError && <p className="text-xs text-expense">{widgetError}</p>}
      <Button variant="secondary" className="w-full" onClick={handleConnect} disabled={connecting}>
        {connecting ? "abrindo..." : "+ conectar banco"}
      </Button>
    </Card>
  );
}
