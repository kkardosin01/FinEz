import { NavLink, Outlet } from "react-router-dom";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Visão geral", icon: "📊" },
  { to: "/transacoes", label: "Transações", icon: "📄" },
  { to: "/orcamentos", label: "Orçamentos", icon: "🎯" },
  { to: "/conta", label: "Conta", icon: "⚙️" },
];

export function AppLayout() {
  return (
    <div className="min-h-screen pb-20 md:pb-0 md:pl-56">
      <nav className="hidden md:fixed md:inset-y-0 md:left-0 md:flex md:w-56 md:flex-col md:border-r md:border-border md:p-4">
        <h1 className="mb-8 text-xl font-bold">FinEz</h1>
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium min-h-[44px]",
                    isActive ? "bg-income/10 text-income" : "text-fg-secondary hover:bg-card"
                  )
                }
              >
                <span aria-hidden>{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <main className="mx-auto max-w-2xl px-4 py-6">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-card md:hidden">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex flex-1 flex-col items-center gap-0.5 py-2 text-xs min-h-[44px]",
                isActive ? "text-income" : "text-fg-secondary"
              )
            }
          >
            <span aria-hidden className="text-lg">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
