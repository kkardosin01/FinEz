import { useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import type { ImportResult } from "./api";
import { useImportTransactions } from "./hooks";

interface ImportTransactionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ImportTransactionsDialog({ open, onOpenChange }: ImportTransactionsDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const importTransactions = useImportTransactions();

  const handleClose = (next: boolean) => {
    if (!next) {
      setFile(null);
      setResult(null);
    }
    onOpenChange(next);
  };

  const handleImport = () => {
    if (!file) return;
    importTransactions.mutate(file, {
      onSuccess: (data) => {
        setResult(data);
        setFile(null);
        if (inputRef.current) inputRef.current.value = "";
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={handleClose} title="Importar planilha">
      <div className="space-y-3">
        <p className="text-sm text-fg-secondary">
          Envie um arquivo .csv ou .xlsx com as colunas <strong>data</strong>,{" "}
          <strong>descrição</strong>, <strong>valor</strong> (negativo pra saída, positivo pra
          entrada) e <strong>categoria</strong> (opcional).
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          onChange={(e) => {
            setResult(null);
            setFile(e.target.files?.[0] ?? null);
          }}
          className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] text-sm"
        />
        {result && (
          <p className="text-sm">
            {result.imported} lançamento{result.imported === 1 ? "" : "s"} importado
            {result.imported === 1 ? "" : "s"}.
            {result.errors.length > 0 && (
              <span className="text-expense"> {result.errors.length} linha(s) com erro.</span>
            )}
          </p>
        )}
        <Button className="w-full" onClick={handleImport} disabled={!file || importTransactions.isPending}>
          {importTransactions.isPending ? "importando..." : "Importar"}
        </Button>
      </div>
    </Dialog>
  );
}
