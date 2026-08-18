import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/app/AppLayout";
import { ProtectedRoute } from "@/app/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { TransactionsPage } from "@/features/transactions/TransactionsPage";
import { BudgetsPage } from "@/features/budgets/BudgetsPage";
import { AccountPage } from "@/features/account/AccountPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/cadastro" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/transacoes" element={<TransactionsPage />} />
        <Route path="/orcamentos" element={<BudgetsPage />} />
        <Route path="/conta" element={<AccountPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
