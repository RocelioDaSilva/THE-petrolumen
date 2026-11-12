import { FormEvent, useEffect, useState } from "react";
import { KeyRound, LoaderCircle, LogIn, UserPlus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useI18n } from "@/lib/i18n";

type AuthMode = "login" | "register";

interface AuthDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (input: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "detail" in error &&
    typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "Authentication failed.";
}

export default function AuthDialog({
  isOpen,
  onClose,
  onLogin,
  onRegister,
}: AuthDialogProps) {
  const { isPt } = useI18n();
  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setError("");
      setMode("login");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isRegister = mode === "register";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      if (isRegister) {
        await onRegister({
          username: username.trim(),
          email: email.trim(),
          password,
          ...(fullName.trim() ? { full_name: fullName.trim() } : {}),
        });
      } else {
        await onLogin(username.trim(), password);
      }
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setError("");
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        aria-label={isPt ? "Fechar autenticação" : "Close authentication"}
        className="absolute inset-0 cursor-default bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-dialog-title"
        className="relative z-10 w-full max-w-md overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
      >
        <div className="border-b border-border bg-background/50 px-6 pb-5 pt-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary">
                {isRegister ? <UserPlus className="h-5 w-5" /> : <KeyRound className="h-5 w-5" />}
              </div>
              <div>
                <h2 id="auth-dialog-title" className="text-lg font-semibold tracking-tight">
                  {isRegister
                    ? isPt ? "Criar conta" : "Create account"
                    : isPt ? "Entrar no PetroLúmen" : "Sign in to PetroLúmen"}
                </h2>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {isPt
                    ? "Entre para salvar e acessar suas simulações."
                    : "Sign in to save and access your simulation runs."}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 shrink-0 text-muted-foreground"
              aria-label={isPt ? "Fechar" : "Close"}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          {isRegister && (
            <>
              <div className="space-y-1.5">
                <Label htmlFor="auth-full-name">{isPt ? "Nome completo (opcional)" : "Full name (optional)"}</Label>
                <Input
                  id="auth-full-name"
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  maxLength={120}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="auth-email">{isPt ? "E-mail" : "Email"}</Label>
                <Input
                  id="auth-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  minLength={5}
                  maxLength={120}
                  required
                />
              </div>
            </>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="auth-username">{isPt ? "Usuário" : "Username"}</Label>
            <Input
              id="auth-username"
              autoComplete={isRegister ? "username" : "username"}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              minLength={isRegister ? 3 : 1}
              maxLength={50}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="auth-password">{isPt ? "Senha" : "Password"}</Label>
            <Input
              id="auth-password"
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={isRegister ? 8 : 1}
              maxLength={128}
              required
            />
            {isRegister && (
              <p className="text-[11px] text-muted-foreground">
                {isPt ? "Use pelo menos 8 caracteres." : "Use at least 8 characters."}
              </p>
            )}
          </div>

          {error && (
            <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
              {error}
            </p>
          )}

          <Button type="submit" className="h-10 w-full gap-2" disabled={isSubmitting}>
            {isSubmitting ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : isRegister ? (
              <UserPlus className="h-4 w-4" />
            ) : (
              <LogIn className="h-4 w-4" />
            )}
            {isSubmitting
              ? isPt ? "Aguarde..." : "Please wait..."
              : isRegister
                ? isPt ? "Criar conta e entrar" : "Create account and sign in"
                : isPt ? "Entrar" : "Sign in"}
          </Button>

          <p className="text-center text-xs text-muted-foreground">
            {isRegister
              ? isPt ? "Já tem uma conta?" : "Already have an account?"
              : isPt ? "Ainda não tem uma conta?" : "Need an account?"}{" "}
            <button
              type="button"
              className="font-medium text-primary underline-offset-4 hover:underline"
              onClick={() => switchMode(isRegister ? "login" : "register")}
            >
              {isRegister
                ? isPt ? "Entrar" : "Sign in"
                : isPt ? "Criar conta" : "Create account"}
            </button>
          </p>
          <p className="text-center text-[10px] text-muted-foreground">
            {isPt
              ? "O token de acesso permanece somente na memória desta sessão."
              : "Your access token is kept in memory for this session only."}
          </p>
        </form>
      </section>
    </div>
  );
}
