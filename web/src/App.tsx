import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/app/AppLayout";
import { ProtectedRoute } from "@/app/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { InsightsPage } from "@/features/insights/InsightsPage";
import { TransactionsPage } from "@/features/transactions/TransactionsPage";
import { BudgetsPage } from "@/features/budgets/BudgetsPage";
import { GoalsPage } from "@/features/goals/GoalsPage";
import { SubscriptionsPage } from "@/features/subscriptions/SubscriptionsPage";
import { InvestmentsPage } from "@/features/investments/InvestmentsPage";
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
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/orcamentos" element={<BudgetsPage />} />
        <Route path="/metas" element={<GoalsPage />} />
        <Route path="/assinaturas" element={<SubscriptionsPage />} />
        <Route path="/investimentos" element={<InvestmentsPage />} />
        <Route path="/conta" element={<AccountPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
