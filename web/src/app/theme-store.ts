import { create } from "zustand";
import type { Theme } from "@/types";

interface ThemeState {
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
}

function resolveSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyThemeClass(resolved: "light" | "dark") {
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

function resolve(theme: Theme): "light" | "dark" {
  return theme === "system" ? resolveSystemTheme() : theme;
}

const initialTheme = (localStorage.getItem("finez-theme") as Theme) || "system";
const initialResolved = resolve(initialTheme);
applyThemeClass(initialResolved);

export const useThemeStore = create<ThemeState>((set) => ({
  theme: initialTheme,
  resolvedTheme: initialResolved,
  setTheme: (theme) => {
    const resolvedTheme = resolve(theme);
    localStorage.setItem("finez-theme", theme);
    applyThemeClass(resolvedTheme);
    set({ theme, resolvedTheme });
  },
}));

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  const { theme, setTheme } = useThemeStore.getState();
  if (theme === "system") setTheme("system");
});
