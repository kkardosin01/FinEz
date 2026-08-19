import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useConnectFlow } from "./useConnectFlow";

interface ConnectBankDialogProps {
  open: boolean;
  onDone: () => void;
}

/** Popup exibido logo após criar a conta, convidando a conectar o banco via Open Finance. */
export function ConnectBankDialog({ open, onDone }: ConnectBankDialogProps) {
  const { connect, connecting, error } = useConnectFlow(onDone);

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onDone()} title="Conecte seu banco">
      <div className="space-y-3">
        <p className="text-sm text-fg-secondary">
          Conecta sua conta via Open Finance e seus gastos do cartão entram sozinhos — sem
          precisar lançar nada manualmente.
        </p>
        {error && <p className="text-xs text-expense">{error}</p>}
        <Button className="w-full" onClick={connect} disabled={connecting}>
          {connecting ? "abrindo..." : "Conectar banco"}
        </Button>
        <Button variant="secondary" className="w-full" onClick={onDone} disabled={connecting}>
          agora não
        </Button>
      </div>
    </Dialog>
  );
}
