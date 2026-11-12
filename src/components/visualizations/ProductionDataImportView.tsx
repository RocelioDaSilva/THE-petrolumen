import { useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileUp,
  Upload,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/authContext";
import {
  importProductionCsv,
  ProductionCsvImportResponse,
} from "@/lib/api";
import {
  MAX_PRODUCTION_CSV_BYTES,
  parseProductionCsv,
  ProductionCsvPreview,
} from "@/lib/productionCsv";
import { useI18n } from "@/lib/i18n";

const PREVIEW_ROW_LIMIT = 20;

export default function ProductionDataImportView() {
  const { isPt } = useI18n();
  const { user, openAuthDialog } = useAuth();
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ProductionCsvPreview | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [result, setResult] = useState<ProductionCsvImportResponse | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const text = isPt
    ? {
        title: "Importação de Produção",
        description:
          "Carregue históricos de produção em CSV para registrar taxas por poço e data.",
        format:
          "Colunas: well_name, date (YYYY-MM-DD) e pelo menos uma entre oil_rate, gas_rate e water_rate.",
        unitsWarning:
          "As taxas são armazenadas como informadas; a tabela atual não registra unidades. Confirme a convenção do projeto antes de importar.",
        drop: "Arraste um arquivo CSV para esta área",
        browse: "Selecionar arquivo CSV",
        inputLabel: "Selecionar arquivo CSV",
        maxSize: "Tamanho máximo: 10 MB. Máximo de 50.000 linhas.",
        selected: "Arquivo selecionado",
        parsing: "Validando arquivo...",
        preview: "Pré-visualização",
        row: "Linha",
        well: "Poço",
        date: "Data",
        oil: "Óleo",
        gas: "Gás",
        water: "Água",
        noRows: "Nenhuma linha válida para exibir.",
        moreRows: "Mostrando",
        of: "de",
        errors: "Erros de validação",
        errorsMore: "erros no total; a lista foi limitada para exibição.",
        commit: "Confirmar importação",
        committing: "Importando...",
        signIn: "Entre na sua conta para importar dados.",
        signInButton: "Entrar",
        success: "Importação concluída",
        imported: "linhas importadas",
        duplicates: "duplicatas ignoradas",
        wellsCreated: "novos poços criados",
        invalidType: "Selecione um arquivo .csv.",
        tooLarge: "O arquivo excede o limite de 10 MB.",
        readError: "Não foi possível ler o arquivo selecionado.",
        requestError: "A importação falhou. Verifique o arquivo e tente novamente.",
      }
    : {
        title: "Production Data Import",
        description:
          "Upload production history CSV files to record rates by well and date.",
        format:
          "Columns: well_name, date (YYYY-MM-DD), and at least one of oil_rate, gas_rate, or water_rate.",
        unitsWarning:
          "Rates are stored as supplied; the current model does not store units. Confirm your project rate convention before importing.",
        drop: "Drop a CSV file in this area",
        browse: "Browse for CSV",
        inputLabel: "Select CSV file",
        maxSize: "Maximum file size: 10 MB. Maximum 50,000 rows.",
        selected: "Selected file",
        parsing: "Validating file...",
        preview: "Data preview",
        row: "Row",
        well: "Well",
        date: "Date",
        oil: "Oil",
        gas: "Gas",
        water: "Water",
        noRows: "No valid rows to preview.",
        moreRows: "Showing",
        of: "of",
        errors: "Validation errors",
        errorsMore: "total errors; the list is limited for display.",
        commit: "Commit import",
        committing: "Importing...",
        signIn: "Sign in to import production data.",
        signInButton: "Sign in",
        success: "Import complete",
        imported: "rows imported",
        duplicates: "duplicates skipped",
        wellsCreated: "new wells created",
        invalidType: "Choose a .csv file.",
        tooLarge: "The file exceeds the 10 MB limit.",
        readError: "Could not read the selected file.",
        requestError: "Import failed. Check the file and try again.",
      };

  const selectFile = async (selected: File | undefined) => {
    if (!selected) return;
    setFile(null);
    setPreview(null);
    setResult(null);
    setSelectionError(null);
    setImportError(null);

    if (!selected.name.toLowerCase().endsWith(".csv")) {
      setSelectionError(text.invalidType);
      return;
    }
    if (selected.size > MAX_PRODUCTION_CSV_BYTES) {
      setSelectionError(text.tooLarge);
      return;
    }

    setFile(selected);
    setIsParsing(true);
    try {
      const contents = new TextDecoder("utf-8", { fatal: true }).decode(
        await selected.arrayBuffer(),
      );
      setPreview(parseProductionCsv(contents));
    } catch {
      setSelectionError(text.readError);
    } finally {
      setIsParsing(false);
    }
  };

  const handleImport = async () => {
    if (!file || !preview || preview.totalErrors > 0 || !user) return;
    setIsImporting(true);
    setImportError(null);
    setResult(null);
    try {
      setResult(await importProductionCsv(file));
    } catch (error) {
      if (typeof error === "object" && error !== null && "detail" in error) {
        setImportError(String(error.detail));
      } else if (error instanceof Error) {
        setImportError(error.message);
      } else {
        setImportError(text.requestError);
      }
    } finally {
      setIsImporting(false);
    }
  };

  const previewRows = preview?.rows.slice(0, PREVIEW_ROW_LIMIT) ?? [];
  const canImport =
    Boolean(user) &&
    Boolean(file) &&
    Boolean(preview?.rows.length) &&
    preview?.totalErrors === 0 &&
    !isParsing &&
    !isImporting;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <FileUp className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{text.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{text.description}</p>
          </div>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>{text.title}</CardTitle>
          <CardDescription>{text.format}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
            {text.unitsWarning}
          </p>
          <div
            className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-muted/20 px-5 py-8 text-center"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              void selectFile(event.dataTransfer.files[0]);
            }}
            aria-label={text.drop}
          >
            <Upload className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
            <p className="text-sm font-medium">{text.drop}</p>
            <input
              ref={fileInput}
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              aria-label={text.inputLabel}
              onChange={(event) => {
                void selectFile(event.target.files?.[0]);
                event.target.value = "";
              }}
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => fileInput.current?.click()}
              disabled={isParsing || isImporting}
            >
              {text.browse}
            </Button>
            <p className="text-xs text-muted-foreground">{text.maxSize}</p>
          </div>

          {selectionError && (
            <p role="alert" className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              {selectionError}
            </p>
          )}
          {file && (
            <p className="text-sm text-muted-foreground">
              {text.selected}: <span className="font-medium text-foreground">{file.name}</span>
            </p>
          )}
          {isParsing && <p role="status" className="text-sm text-muted-foreground">{text.parsing}</p>}

          {preview && (
            <section aria-labelledby="production-csv-preview" className="space-y-3">
              <h2 id="production-csv-preview" className="text-base font-semibold">
                {text.preview}
              </h2>
              {preview.totalErrors > 0 && (
                <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                  <h3 className="mb-2 text-sm font-semibold text-destructive">
                    {text.errors} ({preview.totalErrors})
                  </h3>
                  <ul className="max-h-40 list-inside list-disc space-y-1 overflow-y-auto text-xs text-destructive">
                    {preview.errors.map((error, index) => (
                      <li key={`${error.row}-${index}`}>
                        {text.row} {error.row}: {error.message}
                      </li>
                    ))}
                  </ul>
                  {preview.totalErrors > preview.errors.length && (
                    <p className="mt-2 text-xs text-destructive">
                      {preview.totalErrors} {text.errorsMore}
                    </p>
                  )}
                </div>
              )}

              {previewRows.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-border">
                  <table className="w-full min-w-[640px] text-left text-xs">
                    <thead className="bg-muted/50 text-muted-foreground">
                      <tr>
                        {[text.row, text.well, text.date, text.oil, text.gas, text.water].map((heading) => (
                          <th key={heading} className="px-3 py-2 font-semibold">{heading}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {previewRows.map((row, index) => (
                        <tr key={`${row.well_name}-${row.date}-${index}`} className="font-mono tabular-nums">
                          <td className="px-3 py-2">{index + 2}</td>
                          <td className="px-3 py-2 font-sans">{row.well_name}</td>
                          <td className="px-3 py-2">{row.date}</td>
                          <td className="px-3 py-2">{row.oil_rate ?? "—"}</td>
                          <td className="px-3 py-2">{row.gas_rate ?? "—"}</td>
                          <td className="px-3 py-2">{row.water_rate ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {preview.rows.length > PREVIEW_ROW_LIMIT && (
                    <p className="border-t border-border px-3 py-2 text-xs text-muted-foreground">
                      {text.moreRows} {PREVIEW_ROW_LIMIT} {text.of} {preview.rows.length}
                    </p>
                  )}
                </div>
              ) : (
                <p className="rounded-lg border border-border px-3 py-4 text-sm text-muted-foreground">
                  {text.noRows}
                </p>
              )}
            </section>
          )}

          {!user && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-muted/20 p-3">
              <p className="text-sm text-muted-foreground">{text.signIn}</p>
              <Button type="button" variant="outline" onClick={openAuthDialog}>
                {text.signInButton}
              </Button>
            </div>
          )}

          {importError && (
            <p role="alert" className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              {importError || text.requestError}
            </p>
          )}
          {result && (
            <div role="status" className="rounded-lg border border-primary/30 bg-primary/5 p-3">
              <p className="mb-2 flex items-center gap-2 font-medium text-primary">
                <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                {text.success}
              </p>
              <p className="text-sm text-foreground">
                {result.rows_imported} {text.imported} ·{" "}
                {result.rows_skipped_duplicates} {text.duplicates} ·{" "}
                {result.wells_created} {text.wellsCreated}
              </p>
            </div>
          )}

          <div className="flex justify-end border-t border-border pt-4">
            <Button type="button" onClick={() => void handleImport()} disabled={!canImport}>
              {isImporting ? text.committing : text.commit}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
