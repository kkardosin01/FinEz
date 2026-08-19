import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useConnections, useRevokeConnection } from "./hooks";
import { useConnectFlow } from "./useConnectFlow";

const STATUS_LABEL: Record<string, string> = {
  syncing: "sincronizando...",
  active: "ativa",
  error: "erro na sincronização",
  revoked: "revogada",
};

export function ConnectionsSection() {
  const { data: connections } = useConnections();
  const revoke = useRevokeConnection();
  const { connect, connecting, error } = useConnectFlow();

  return (
    <Card className="space-y-3">
      <h2 className="font-heading font-semibold">Open Finance — bancos conectados</h2>
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
      {error && <p className="text-xs text-expense">{error}</p>}
      <Button variant="secondary" className="w-full" onClick={connect} disabled={connecting}>
        {connecting ? "abrindo..." : "+ conectar banco"}
      </Button>
    </Card>
  );
}
