import { zodResolver } from "@hookform/resolvers/zod";
import type { ReactNode } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { useRegister } from "./hooks";

const schema = z.object({
  invite_code: z.string().min(1, "código de convite é obrigatório"),
  name: z.string().min(1, "digite seu nome"),
  email: z.string().email("email inválido"),
  password: z.string().min(8, "mínimo de 8 caracteres"),
  birth_date: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const registerUser = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormData) => {
    registerUser.mutate(data, {
      onSuccess: () => navigate("/"),
      onError: (err) => {
        const message =
          err instanceof ApiError
            ? Object.values(err.body as Record<string, string[]>)[0]?.[0] ?? "não foi possível criar a conta"
            : "não foi possível criar a conta";
        setError("root", { message });
      },
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Criar conta</h1>
          <p className="text-sm text-fg-secondary">beta fechado — precisa de um código de convite</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Field label="Código de convite" error={errors.invite_code?.message}>
            <input
              placeholder="FINEZ-A3X9"
              className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px] uppercase"
              {...register("invite_code")}
            />
          </Field>
          <Field label="Nome" error={errors.name?.message}>
            <input className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("name")} />
          </Field>
          <Field label="Email" error={errors.email?.message}>
            <input type="email" className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("email")} />
          </Field>
          <Field label="Senha" error={errors.password?.message}>
            <input type="password" className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("password")} />
          </Field>
          <Field
            label="Data de nascimento (opcional)"
            hint="só usamos pra cumprir a LGPD com menores de 18 — não afeta o uso do bot"
            error={errors.birth_date?.message}
          >
            <input type="date" className="w-full rounded-lg border border-border bg-bg px-3 py-2 min-h-[44px]" {...register("birth_date")} />
          </Field>
          {errors.root && <p className="text-sm text-expense">{errors.root.message}</p>}
          <Button type="submit" className="w-full" disabled={registerUser.isPending}>
            {registerUser.isPending ? "criando..." : "Criar conta"}
          </Button>
        </form>
        <p className="text-center text-sm text-fg-secondary">
          já tem conta?{" "}
          <Link to="/login" className="text-income font-medium">
            entrar
          </Link>
        </p>
      </Card>
    </div>
  );
}

function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium">{label}</label>
      {children}
      {hint && !error && <p className="text-xs text-fg-secondary">{hint}</p>}
      {error && <p className="text-xs text-expense">{error}</p>}
    </div>
  );
}
