import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { api, API_URL } from "@/lib/api";
import { useMe, useLogout } from "@/features/auth/hooks";
import { ConnectionsSection } from "@/features/connections/ConnectionsPage";
import { useGeneratePairingCode, usePairingStatus } from "./hooks";

export function AccountPage() {
  const navigate = useNavigate();
  const { data: me } = useMe();
  const logout = useLogout();
  const { data: pairing } = usePairingStatus();
  const generatePairingCode = useGeneratePairingCode();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete("/me");
      navigate("/login");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-xl font-semibold">Conta</h1>

      <Card className="space-y-2">
        <p className="text-sm text-fg-secondary">Logado como</p>
        <p className="font-medium">{me?.name ?? me?.email}</p>
        <p className="text-sm text-fg-secondary">{me?.email}</p>
      </Card>

      <Card className="space-y-3">
        <h2 className="font-heading font-semibold">WhatsApp</h2>
        {pairing?.status === "active" ? (
          <p className="text-sm text-fg-secondary">
            Conectado ao número <span className="font-mono">{pairing.phone_e164}</span>
          </p>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-fg-secondary">
              Manda o código abaixo pro nosso número no WhatsApp pra parear sua conta.
            </p>
            {pairing?.pairing_code && (
              <p className="rounded-lg bg-bg px-3 py-2 text-center font-mono text-lg tracking-widest">
                {pairing.pairing_code}
              </p>
            )}
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => generatePairingCode.mutate()}
              disabled={generatePairingCode.isPending}
            >
              {pairing?.pairing_code ? "gerar novo código" : "gerar código de pareamento"}
            </Button>
          </div>
        )}
      </Card>

      <ConnectionsSection />

      <Card className="space-y-3">
        <h2 className="font-heading font-semibold">Exportar dados</h2>
        <div className="flex gap-2">
          <a
            href={`${API_URL}/exports/csv`}
            className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 min-h-[44px] text-sm font-medium hover:bg-bg"
          >
            CSV
          </a>
          <a
            href={`${API_URL}/exports/xlsx`}
            className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 min-h-[44px] text-sm font-medium hover:bg-bg"
          >
            XLSX
          </a>
        </div>
      </Card>

      <Card className="space-y-3">
        <Button variant="secondary" className="w-full" onClick={() => logout.mutate()}>
          Sair
        </Button>
        <Button variant="danger" className="w-full" onClick={() => setDeleteOpen(true)}>
          Excluir minha conta
        </Button>
      </Card>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen} title="Excluir conta">
        <div className="space-y-3">
          <p className="text-sm text-fg-secondary">
            Isso apaga permanentemente seus lançamentos, contas conectadas e orçamentos — não dá
            pra desfazer. Digite <strong>excluir</strong> pra confirmar.
          </p>
          <input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]"
          />
          <Button
            variant="danger"
            className="w-full"
            disabled={confirmText !== "excluir" || deleting}
            onClick={handleDelete}
          >
            {deleting ? "excluindo..." : "excluir permanentemente"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
