import { useThemeStore } from "@/app/theme-store";
import { cn } from "@/lib/utils";

interface CategoryChipProps {
  name: string;
  colorLight: string;
  colorDark: string;
  onClick?: () => void;
  active?: boolean;
}

/** Chip de categoria — clicável = recategorizar (seção 2). */
export function CategoryChip({ name, colorLight, colorDark, onClick, active }: CategoryChipProps) {
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme);
  const color = resolvedTheme === "dark" ? colorDark : colorLight;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium min-h-[32px] transition-opacity",
        active ? "border-transparent text-white" : "border-border text-fg hover:opacity-80"
      )}
      style={active ? { backgroundColor: color } : undefined}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden
      />
      {name}
    </button>
  );
}
