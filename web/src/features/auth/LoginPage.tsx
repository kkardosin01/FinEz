import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { useLogin } from "./hooks";

const schema = z.object({
  email: z.string().email("email inválido"),
  password: z.string().min(1, "digite sua senha"),
});
type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormData) => {
    login.mutate(data, {
      onSuccess: () => navigate("/"),
      onError: (err) => {
        const message =
          err instanceof ApiError ? String((err.body as { non_field_errors?: string[] })?.non_field_errors?.[0] ?? "não foi possível entrar") : "não foi possível entrar";
        setError("root", { message });
      },
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-6">
        <div>
          <h1 className="text-2xl font-bold">FinEz</h1>
          <p className="text-sm text-fg-secondary">conecte uma vez, entenda pra sempre</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-income"
              {...register("email")}
            />
            {errors.email && <p className="text-xs text-expense">{errors.email.message}</p>}
          </div>
          <div className="space-y-1">
            <label htmlFor="password" className="text-sm font-medium">
              Senha
            </label>
            <input
              id="password"
              type="password"
              className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-income"
              {...register("password")}
            />
            {errors.password && <p className="text-xs text-expense">{errors.password.message}</p>}
          </div>
          {errors.root && <p className="text-sm text-expense">{errors.root.message}</p>}
          <Button type="submit" className="w-full" disabled={login.isPending}>
            {login.isPending ? "entrando..." : "Entrar"}
          </Button>
        </form>
        <p className="text-center text-sm text-fg-secondary">
          novo por aqui?{" "}
          <Link to="/cadastro" className="text-income font-medium">
            cadastre-se com um convite
          </Link>
        </p>
      </Card>
    </div>
  );
}
