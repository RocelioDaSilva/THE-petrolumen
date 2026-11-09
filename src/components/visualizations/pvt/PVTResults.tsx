import type { PVTResults as PVTProperties } from "@/lib/reservoirMath";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface PVTTableRow {
  pressure: number;
  temperature: number;
  results: PVTProperties;
}

const columns: Array<{
  label: string;
  value: (row: PVTTableRow) => number;
}> = [
  { label: "Pressure (psia)", value: (row) => row.pressure },
  { label: "Temperature (°F)", value: (row) => row.temperature },
  { label: "Z-factor", value: (row) => row.results.zFactor },
  { label: "Oil FVF (Bo)", value: (row) => row.results.bo },
  { label: "Gas FVF (Bg)", value: (row) => row.results.bg },
  { label: "Solution GOR (Rs)", value: (row) => row.results.rs },
  { label: "Bubble point (Pb)", value: (row) => row.results.pb },
  { label: "Oil viscosity (cP)", value: (row) => row.results.oilViscosity },
];

export function formatPVTResultsCsv(rows: PVTTableRow[]): string {
  const header = columns.map((column) => column.label).join(",");
  const values = rows.map((row) =>
    columns.map((column) => column.value(row).toPrecision(10)).join(","),
  );
  return [header, ...values].join("\r\n");
}

interface PVTResultsProps {
  rows: PVTTableRow[];
  onExportCsv: (csv: string) => void;
}

export function PVTResults({ rows, onExportCsv }: PVTResultsProps) {
  if (rows.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="text-base">PVT analysis results</CardTitle>
        <Button
          type="button"
          variant="outline"
          onClick={() => onExportCsv(formatPVTResultsCsv(rows))}
        >
          Export CSV
        </Button>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                {columns.map((column) => (
                  <th key={column.label} className="whitespace-nowrap px-3 py-2">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.pressure}-${row.temperature}`} className="border-b">
                  {columns.map((column) => (
                    <td key={column.label} className="whitespace-nowrap px-3 py-2">
                      {column.value(row).toPrecision(6)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
