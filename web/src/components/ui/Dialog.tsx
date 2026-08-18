import * as RadixDialog from "@radix-ui/react-dialog";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Dialog({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 bg-black/40 z-20" />
        <RadixDialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-30 w-full max-w-sm -translate-x-1/2 -translate-y-1/2",
            "rounded-card bg-card border border-border p-4 space-y-4"
          )}
        >
          <RadixDialog.Title className="font-heading text-lg font-semibold">{title}</RadixDialog.Title>
          {children}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
