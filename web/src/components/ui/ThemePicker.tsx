import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { useThemeStore } from "@/app/theme-store";
import { useUpdateTheme } from "@/features/account/hooks";
import type { Theme } from "@/types";
import { cn } from "@/lib/utils";

const THEME_OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: "light", label: "Claro", icon: "☀️" },
  { value: "dark", label: "Escuro", icon: "🌙" },
  { value: "system", label: "Padrão do sistema", icon: "🖥️" },
];

interface ThemePickerProps {
  className?: string;
}

/** Seletor de tema inline — vive no rodapé da sidebar (seção 3 do pedido de UX). */
export function ThemePicker({ className }: ThemePickerProps) {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);
  const updateTheme = useUpdateTheme();
  const current = THEME_OPTIONS.find((opt) => opt.value === theme) ?? THEME_OPTIONS[2];

  const handleSelect = (value: Theme) => {
    setTheme(value);
    updateTheme.mutate(value);
  };

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className={cn(
            "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium min-h-[44px] text-fg-secondary hover:bg-card",
            className
          )}
        >
          <span aria-hidden>{current.icon}</span>
          Aparência
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          side="top"
          align="start"
          sideOffset={8}
          className="z-30 min-w-[200px] rounded-lg border border-border bg-card p-1 shadow-lg"
        >
          {THEME_OPTIONS.map((opt) => (
            <DropdownMenu.Item
              key={opt.value}
              onSelect={() => handleSelect(opt.value)}
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm outline-none min-h-[40px]",
                theme === opt.value ? "bg-income/10 text-income" : "text-fg hover:bg-bg"
              )}
            >
              <span aria-hidden>{opt.icon}</span>
              {opt.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
