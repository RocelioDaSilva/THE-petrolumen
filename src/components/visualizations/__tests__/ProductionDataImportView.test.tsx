import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  importProductionCsv: vi.fn(),
  auth: {
    user: { id: 2, username: "engineer" } as null | { id: number; username: string },
    openAuthDialog: vi.fn(),
  },
}));

vi.mock("@/lib/api", () => ({
  importProductionCsv: mocks.importProductionCsv,
}));

vi.mock("@/lib/authContext", () => ({
  useAuth: () => mocks.auth,
}));

import ProductionDataImportView from "../ProductionDataImportView";

function csvFile(contents: string, name = "production.csv"): File {
  const file = new File([contents], name, { type: "text/csv" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new Blob([contents]).arrayBuffer(),
  });
  return file;
}

describe("ProductionDataImportView", () => {
  beforeEach(() => {
    mocks.auth.user = { id: 2, username: "engineer" };
    mocks.importProductionCsv.mockReset().mockResolvedValue({
      rows_received: 2,
      rows_imported: 2,
      rows_skipped_duplicates: 0,
      wells_created: 1,
    });
    mocks.auth.openAuthDialog.mockReset();
  });

  it("previews a valid file and submits it to the import API", async () => {
    const file = csvFile(
      "well_name,date,oil_rate,gas_rate,water_rate\nWell A,2025-01-01,10,,2\nWell A,2025-02-01,8,,3\n",
    );
    render(<ProductionDataImportView />);

    fireEvent.change(screen.getByLabelText("Selecionar arquivo CSV"), {
      target: { files: [file] },
    });

    expect(await screen.findAllByText("Well A")).toHaveLength(2);
    const commit = screen.getByRole("button", { name: "Confirmar importação" });
    expect(commit).toBeEnabled();
    fireEvent.click(commit);

    await waitFor(() => expect(mocks.importProductionCsv).toHaveBeenCalledWith(file));
    expect(await screen.findByText("Importação concluída")).toBeInTheDocument();
    expect(screen.getByText(/2 linhas importadas/)).toBeInTheDocument();
  });

  it("shows validation errors and blocks imports when rows are invalid", async () => {
    const file = csvFile("well_name,date,oil_rate\nWell A,2025-02-30,10\n");
    render(<ProductionDataImportView />);

    fireEvent.change(screen.getByLabelText("Selecionar arquivo CSV"), {
      target: { files: [file] },
    });

    expect(await screen.findByText(/date must be a valid YYYY-MM-DD/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar importação" })).toBeDisabled();
    expect(mocks.importProductionCsv).not.toHaveBeenCalled();
  });

  it("supports dropping a file and prompts signed-out users to authenticate", async () => {
    mocks.auth.user = null;
    const file = csvFile("well_name,date,oil_rate\nWell A,2025-01-01,10\n");
    render(<ProductionDataImportView />);

    fireEvent.drop(screen.getByLabelText("Arraste um arquivo CSV para esta área"), {
      dataTransfer: { files: [file] },
    });

    expect(await screen.findByText("Well A")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(mocks.auth.openAuthDialog).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "Confirmar importação" })).toBeDisabled();
  });
});
