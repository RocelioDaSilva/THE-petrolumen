import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface PVTFormValues {
  pressure: number;
  temperature: number;
  gasGravity: number;
  apiGravity: number;
  gor: number;
}

export interface PVTTableRange {
  start: number;
  end: number;
  step: number;
}

interface PVTInputFormProps {
  values: PVTFormValues;
  pressureUnit: string;
  temperatureUnit: string;
  canGenerateTable: boolean;
  generatedRowCount: number;
  onChange: (field: keyof PVTFormValues, value: number) => void;
  onGenerateTable: (range: PVTTableRange) => void;
}

const MAX_TABLE_ROWS = 500;

export function PVTInputForm({
  values,
  pressureUnit,
  temperatureUnit,
  canGenerateTable,
  generatedRowCount,
  onChange,
  onGenerateTable,
}: PVTInputFormProps) {
  const [range, setRange] = useState<PVTTableRange>({
    start: 500,
    end: 6000,
    step: 250,
  });
  const rowCount =
    range.step > 0 && range.end >= range.start
      ? Math.floor((range.end - range.start) / range.step) + 1
      : 0;
  const validRange =
    Number.isFinite(range.start) &&
    Number.isFinite(range.end) &&
    Number.isFinite(range.step) &&
    rowCount > 0 &&
    rowCount <= MAX_TABLE_ROWS;

  const updateRange = (field: keyof PVTTableRange, value: string) => {
    const numericValue = Number(value);
    setRange((current) => ({
      ...current,
      [field]: Number.isFinite(numericValue) ? numericValue : 0,
    }));
  };

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label htmlFor="pvt-p">Pressure ({pressureUnit})</Label>
          <span className="text-xs font-mono font-bold text-primary">
            {values.pressure}
          </span>
        </div>
        <Input
          id="pvt-p"
          type="number"
          value={values.pressure}
          onChange={(event) => onChange("pressure", Number(event.target.value))}
          className={values.pressure <= 0 ? "border-red-500" : ""}
        />
        <p className="text-[10px] text-muted-foreground">
          Single-point properties update as parameters change.
        </p>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label htmlFor="pvt-t">Temperature ({temperatureUnit})</Label>
          <span className="text-xs font-mono font-bold text-primary">
            {values.temperature}
          </span>
        </div>
        <Input
          id="pvt-t"
          type="number"
          value={values.temperature}
          onChange={(event) =>
            onChange("temperature", Number(event.target.value))
          }
          className={values.temperature <= -459.67 ? "border-red-500" : ""}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pvt-gammag">Gas specific gravity (air = 1.0)</Label>
        <Input
          id="pvt-gammag"
          type="number"
          step="0.01"
          value={values.gasGravity}
          onChange={(event) => onChange("gasGravity", Number(event.target.value))}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pvt-api">Oil API gravity (°API)</Label>
        <Input
          id="pvt-api"
          type="number"
          step="0.5"
          value={values.apiGravity}
          onChange={(event) => onChange("apiGravity", Number(event.target.value))}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pvt-gor">Gas-oil ratio (scf/STB)</Label>
        <Input
          id="pvt-gor"
          type="number"
          step="10"
          value={values.gor}
          onChange={(event) => onChange("gor", Number(event.target.value))}
        />
      </div>

      <fieldset className="space-y-3 border-t pt-4">
        <legend className="text-sm font-semibold">Generate PVT table</legend>
        <div className="grid grid-cols-3 gap-2">
          {(
            [
              ["start", "Start pressure"],
              ["end", "End pressure"],
              ["step", "Pressure step"],
            ] as const
          ).map(([field, label]) => (
            <label key={field} className="space-y-1 text-xs">
              <span>{label}</span>
              <Input
                type="number"
                aria-label={label}
                value={range[field]}
                onChange={(event) => updateRange(field, event.target.value)}
              />
            </label>
          ))}
        </div>
        {!validRange && (
          <p role="alert" className="text-xs text-red-600">
            Enter a positive pressure step and a valid range with at most{" "}
            {MAX_TABLE_ROWS} rows.
          </p>
        )}
        <Button
          type="button"
          variant="outline"
          className="w-full"
          disabled={!validRange || !canGenerateTable}
          onClick={() => onGenerateTable(range)}
        >
          Generate {rowCount} table points
        </Button>
        {generatedRowCount > 0 && (
          <p role="status" className="text-xs text-muted-foreground">
            Generated {generatedRowCount} PVT table points.
          </p>
        )}
      </fieldset>
    </div>
  );
}
