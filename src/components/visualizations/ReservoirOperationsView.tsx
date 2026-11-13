import { useState } from "react";
import { Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  calculateReservoirOperation,
  ReservoirOperationPath,
  ReservoirOperationResult,
} from "@/lib/api";

interface NumericField {
  key: string;
  label: string;
  initial: number;
  step?: string;
}

interface OperationDefinition {
  path: ReservoirOperationPath;
  label: string;
  description: string;
  fields: NumericField[];
}

const operations: OperationDefinition[] = [
  {
    path: "choke/gilbert",
    label: "Gilbert choke",
    description: "Estimate wellhead pressure from liquid rate, GLR, and choke size.",
    fields: [
      { key: "q_bpd", label: "Liquid rate (STB/day)", initial: 1000 },
      { key: "glr", label: "Gas-liquid ratio (scf/STB)", initial: 600 },
      { key: "choke_64", label: "Choke size (1/64 in)", initial: 32 },
    ],
  },
  {
    path: "choke/critical-ratio",
    label: "Critical gas pressure ratio",
    description: "Calculate the critical pressure ratio for compressible gas flow.",
    fields: [{ key: "k", label: "Heat capacity ratio Cp/Cv", initial: 1.28, step: "any" }],
  },
  {
    path: "choke/sonic-gas",
    label: "Sonic gas choke",
    description: "Calculate critical gas flow through a choke.",
    fields: [
      { key: "cd", label: "Discharge coefficient", initial: 0.6, step: "any" },
      { key: "A2_in2", label: "Throat area (in²)", initial: 0.05, step: "any" },
      { key: "p_up", label: "Upstream pressure (psia)", initial: 1000 },
      { key: "t_up_R", label: "Upstream temperature (°R)", initial: 520 },
      { key: "gamma_g", label: "Gas specific gravity", initial: 0.65, step: "any" },
      { key: "k", label: "Heat capacity ratio Cp/Cv", initial: 1.28, step: "any" },
    ],
  },
  {
    path: "choke/subsonic-gas",
    label: "Subsonic gas choke",
    description: "Calculate subcritical gas flow through a choke.",
    fields: [
      { key: "cd", label: "Discharge coefficient", initial: 0.6, step: "any" },
      { key: "A2_in2", label: "Throat area (in²)", initial: 0.05, step: "any" },
      { key: "p_up", label: "Upstream pressure (psia)", initial: 1000 },
      { key: "t_up_R", label: "Upstream temperature (°R)", initial: 520 },
      { key: "gamma_g", label: "Gas specific gravity", initial: 0.65, step: "any" },
      { key: "k", label: "Heat capacity ratio Cp/Cv", initial: 1.28, step: "any" },
      { key: "p_dn", label: "Downstream pressure (psia)", initial: 300 },
    ],
  },
  {
    path: "tubing/collapse-biaxial",
    label: "Biaxial tubing collapse",
    description: "Apply the biaxial stress correction to collapse pressure.",
    fields: [
      { key: "p_c", label: "Collapse pressure (psi)", initial: 5000 },
      { key: "sa", label: "Axial stress (psi)", initial: 10000 },
      { key: "ym", label: "Yield strength (psi)", initial: 80000 },
    ],
  },
  {
    path: "tubing/ballooning",
    label: "Tubing ballooning",
    description: "Estimate length change caused by internal and external pressure changes.",
    fields: [
      { key: "dpi", label: "Internal pressure change (psi)", initial: 500 },
      { key: "dpo", label: "External pressure change (psi)", initial: 100 },
      { key: "A_i", label: "Inside area (in²)", initial: 2, step: "any" },
      { key: "A_o", label: "Outside area (in²)", initial: 3, step: "any" },
      { key: "L", label: "Tubing length (ft)", initial: 1000 },
    ],
  },
  {
    path: "tubing/piston",
    label: "Tubing piston effect",
    description: "Estimate piston force and tubing length change at the packer.",
    fields: [
      { key: "pi_c", label: "Internal pressure at packer (psi)", initial: 3000 },
      { key: "po_c", label: "External pressure at packer (psi)", initial: 1000 },
      { key: "A_p", label: "Packer bore area (in²)", initial: 5, step: "any" },
      { key: "A_i", label: "Tubing inside area (in²)", initial: 4, step: "any" },
      { key: "A_o", label: "Tubing outside area (in²)", initial: 5, step: "any" },
      { key: "L", label: "Tubing length (ft)", initial: 10000 },
      { key: "E", label: "Young's modulus (psi)", initial: 30000000 },
      { key: "A_s", label: "Steel cross-section (in²)", initial: 3, step: "any" },
    ],
  },
  {
    path: "tubing/bending-stress",
    label: "Tubing bending stress",
    description: "Calculate bending stress for tubing in a curved well section.",
    fields: [
      { key: "E", label: "Young's modulus (psi)", initial: 30000000 },
      { key: "Do", label: "Outside diameter (in)", initial: 2.875, step: "any" },
      { key: "Rc", label: "Curvature radius (in)", initial: 1000 },
    ],
  },
  {
    path: "gas-lift/valve-depth",
    label: "Gas-lift unloading valve depth",
    description: "Estimate the first unloading valve depth.",
    fields: [
      { key: "pk_s", label: "Surface kickoff pressure (psia)", initial: 1200 },
      { key: "dp_km", label: "Pressure increment per valve (psi)", initial: 50 },
      { key: "phf", label: "Flowing wellhead pressure (psia)", initial: 500 },
      { key: "Gs", label: "Gas gradient (psi/ft)", initial: 0.02, step: "any" },
    ],
  },
  {
    path: "gas-lift/valve-open-close",
    label: "Gas-lift valve opening and closing",
    description: "Calculate gas-lift valve opening and closing pressures.",
    fields: [
      { key: "pd", label: "Dome pressure (psia)", initial: 1200 },
      { key: "St", label: "Spring tension (psi)", initial: 50 },
      { key: "R", label: "Area ratio Ab/Ap", initial: 0.8, step: "any" },
      { key: "pt", label: "Tubing pressure (psia)", initial: 500 },
    ],
  },
  {
    path: "gas-lift/orifice-size",
    label: "Gas-lift orifice sizing",
    description: "Size an orifice for a target gas rate and pressure drop.",
    fields: [
      { key: "q_mscfd", label: "Gas rate (Mscf/day)", initial: 5, step: "any" },
      { key: "p_up", label: "Upstream pressure (psia)", initial: 1000 },
      { key: "p_dn", label: "Downstream pressure (psia)", initial: 300 },
      { key: "gg", label: "Gas specific gravity", initial: 0.65, step: "any" },
      { key: "t_R", label: "Temperature (°R)", initial: 520 },
      { key: "k", label: "Heat capacity ratio Cp/Cv", initial: 1.28, step: "any" },
      { key: "cd", label: "Discharge coefficient", initial: 0.6, step: "any" },
    ],
  },
  {
    path: "gas-lift/injection-glr",
    label: "Gas-lift injection GLR",
    description: "Estimate required injection GLR from optimum and formation GLR.",
    fields: [
      { key: "glr_opt", label: "Optimum GLR (scf/STB)", initial: 600 },
      { key: "glr_form", label: "Formation GLR (scf/STB)", initial: 300 },
    ],
  },
];

function getErrorMessage(error: unknown): string {
  if (
    typeof error === "object"
    && error !== null
    && "detail" in error
    && typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The calculation could not be completed.";
}

export default function ReservoirOperationsView() {
  const [selectedPath, setSelectedPath] = useState<ReservoirOperationPath>(operations[0].path);
  const [values, setValues] = useState<Record<string, number>>(
    Object.fromEntries(operations[0].fields.map(({ key, initial }) => [key, initial])),
  );
  const [result, setResult] = useState<ReservoirOperationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const operation = operations.find(({ path }) => path === selectedPath) ?? operations[0];

  const selectOperation = (path: ReservoirOperationPath) => {
    const selected = operations.find((candidate) => candidate.path === path);
    if (!selected) return;
    setSelectedPath(path);
    setValues(Object.fromEntries(selected.fields.map(({ key, initial }) => [key, initial])));
    setResult(null);
    setError(null);
  };

  const calculate = async () => {
    setIsLoading(true);
    setResult(null);
    setError(null);
    try {
      setResult(await calculateReservoirOperation(selectedPath, values));
    } catch (calculationError) {
      setError(getErrorMessage(calculationError));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h2 className="flex items-center gap-2 text-2xl font-bold">
          <Activity className="h-6 w-6 text-primary" />
          Choke, Tubing, and Gas-Lift Calculations
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Run the existing validated backend calculations for production operations.
          All fields and units correspond to the API request schemas.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Select calculation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="reservoir-operation">Calculation</Label>
            <Select
              id="reservoir-operation"
              value={selectedPath}
              onChange={(event) => {
                const selected = operations.find(({ path }) => path === event.target.value);
                if (selected) selectOperation(selected.path);
              }}
            >
              {operations.map(({ path, label }) => (
                <option key={path} value={path}>{label}</option>
              ))}
            </Select>
          </div>
          <p className="text-sm text-muted-foreground">{operation.description}</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {operation.fields.map((field) => (
              <div key={field.key} className="space-y-1.5">
                <Label htmlFor={`operation-${field.key}`}>{field.label}</Label>
                <Input
                  id={`operation-${field.key}`}
                  type="number"
                  step={field.step}
                  value={values[field.key] ?? field.initial}
                  onChange={(event) => setValues((current) => ({
                    ...current,
                    [field.key]: Number(event.target.value),
                  }))}
                />
              </div>
            ))}
          </div>
          <Button type="button" onClick={calculate} disabled={isLoading}>
            {isLoading ? "Calculating..." : "Calculate"}
          </Button>
        </CardContent>
      </Card>

      {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}

      {result && (
        <Card aria-label="Calculation result">
          <CardHeader><CardTitle className="text-base">Backend result</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(result).map(([key, value]) => (
              <div key={key} className="rounded-md border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">{key.replace(/_/g, " ")}</p>
                <p className="mt-1 font-mono text-lg font-semibold">
                  {typeof value === "number" ? value.toPrecision(5) : value}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
