import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AuthDialog from "../AuthDialog";
import { I18nProvider } from "@/lib/i18n";

describe("AuthDialog", () => {
  it("supports switching from sign in to account creation", () => {
    render(
      <I18nProvider>
        <AuthDialog
          isOpen
          onClose={vi.fn()}
          onLogin={vi.fn().mockResolvedValue(undefined)}
          onRegister={vi.fn().mockResolvedValue(undefined)}
        />
      </I18nProvider>,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByLabelText("Nome completo (opcional)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Criar conta e entrar" })).toBeInTheDocument();
  });

  it("displays authentication errors instead of hiding them", async () => {
    const onLogin = vi.fn().mockRejectedValue({ status: 401, detail: "Incorrect username or password." });
    render(
      <I18nProvider>
        <AuthDialog isOpen onClose={vi.fn()} onLogin={onLogin} onRegister={vi.fn()} />
      </I18nProvider>,
    );

    fireEvent.change(screen.getByLabelText("Usuário"), { target: { value: "engineer" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "wrong-password" } });
    fireEvent.submit(screen.getByRole("dialog").querySelector("form")!);

    expect(await screen.findByRole("alert")).toHaveTextContent("Incorrect username or password.");
  });
});
