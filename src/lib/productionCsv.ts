export const MAX_PRODUCTION_CSV_BYTES = 10 * 1024 * 1024;
export const MAX_PRODUCTION_CSV_ROWS = 50_000;

const RATE_COLUMNS = ["oil_rate", "gas_rate", "water_rate"] as const;

export interface ProductionCsvRow {
  well_name: string;
  date: string;
  oil_rate: number | null;
  gas_rate: number | null;
  water_rate: number | null;
}

export interface ProductionCsvError {
  row: number;
  message: string;
}

export interface ProductionCsvPreview {
  rows: ProductionCsvRow[];
  errors: ProductionCsvError[];
  totalErrors: number;
}

function readCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let insideQuotes = false;
  let afterQuote = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];

    if (insideQuotes) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        insideQuotes = false;
        afterQuote = true;
      } else {
        field += character;
      }
      continue;
    }

    if (afterQuote && character.trim() !== "" && character !== "," && character !== "\r" && character !== "\n") {
      throw new Error("Unexpected character after a quoted CSV field.");
    }
    if (character === '"') {
      if (field.length > 0) throw new Error("Unexpected quote in an unquoted CSV field.");
      insideQuotes = true;
      afterQuote = false;
    } else if (character === ",") {
      row.push(field);
      field = "";
      afterQuote = false;
    } else if (character === "\r" || character === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      afterQuote = false;
      if (character === "\r" && text[index + 1] === "\n") index += 1;
    } else if (!afterQuote) {
      field += character;
    }
  }

  if (insideQuotes) throw new Error("CSV contains an unterminated quoted field.");
  if (field.length > 0 || row.length > 0 || afterQuote) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function isIsoCalendarDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  if (year < 1) return false;
  const date = new Date(0);
  date.setUTCHours(0, 0, 0, 0);
  date.setUTCFullYear(year, month - 1, day);
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() === month - 1 &&
    date.getUTCDate() === day
  );
}

export function parseProductionCsv(text: string): ProductionCsvPreview {
  let csvRows: string[][];
  try {
    csvRows = readCsvRows(text.replace(/^\uFEFF/, "")).filter((row) =>
      row.some((value) => value.trim() !== ""),
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not parse CSV.";
    return { rows: [], errors: [{ row: 1, message }], totalErrors: 1 };
  }

  const rawHeaders = csvRows[0];
  if (!rawHeaders) {
    return {
      rows: [],
      errors: [{ row: 1, message: "CSV is empty." }],
      totalErrors: 1,
    };
  }

  const headers = rawHeaders.map((header) => header.trim().toLowerCase());
  if (headers.some((header) => !header) || new Set(headers).size !== headers.length) {
    return {
      rows: [],
      errors: [{ row: 1, message: "CSV headers must be non-empty and unique." }],
      totalErrors: 1,
    };
  }

  const missingHeaders = ["well_name", "date"].filter(
    (header) => !headers.includes(header),
  );
  if (missingHeaders.length > 0) {
    return {
      rows: [],
      errors: [
        {
          row: 1,
          message: `CSV is missing required columns: ${missingHeaders.join(", ")}.`,
        },
      ],
      totalErrors: 1,
    };
  }
  if (!RATE_COLUMNS.some((column) => headers.includes(column))) {
    return {
      rows: [],
      errors: [
        {
          row: 1,
          message: `CSV must include at least one rate column: ${RATE_COLUMNS.join(", ")}.`,
        },
      ],
      totalErrors: 1,
    };
  }
  if (csvRows.length - 1 > MAX_PRODUCTION_CSV_ROWS) {
    return {
      rows: [],
      errors: [
        {
          row: 1,
          message: `CSV exceeds the ${MAX_PRODUCTION_CSV_ROWS.toLocaleString()}-row limit.`,
        },
      ],
      totalErrors: 1,
    };
  }

  const rows: ProductionCsvRow[] = [];
  const errors: ProductionCsvError[] = [];
  let totalErrors = 0;
  const addError = (rowNumber: number, message: string) => {
    totalErrors += 1;
    if (errors.length < 100) errors.push({ row: rowNumber, message });
  };

  csvRows.slice(1).forEach((values, index) => {
    const rowNumber = index + 2;
    if (values.length !== headers.length) {
      addError(rowNumber, "Column count does not match the CSV header.");
      return;
    }

    const row = Object.fromEntries(
      headers.map((header, headerIndex) => [header, values[headerIndex].trim()]),
    );
    const rowErrors: string[] = [];
    const wellName = row.well_name;
    if (!wellName) rowErrors.push("well_name is required.");
    else if (wellName.length > 120) {
      rowErrors.push("well_name must be at most 120 characters.");
    }

    const date = row.date;
    if (!isIsoCalendarDate(date)) {
      rowErrors.push("date must be a valid YYYY-MM-DD calendar date.");
    }

    const rates: Record<(typeof RATE_COLUMNS)[number], number | null> = {
      oil_rate: null,
      gas_rate: null,
      water_rate: null,
    };
    for (const column of RATE_COLUMNS) {
      const value = row[column] ?? "";
      if (!value) continue;
      const rate = Number(value);
      if (!Number.isFinite(rate) || rate < 0) {
        rowErrors.push(`${column} must be a finite non-negative number.`);
      } else {
        rates[column] = rate;
      }
    }
    if (!Object.values(rates).some((rate) => rate !== null)) {
      rowErrors.push("At least one production rate is required per row.");
    }

    if (rowErrors.length > 0) {
      rowErrors.forEach((message) => addError(rowNumber, message));
    } else {
      rows.push({ well_name: wellName, date, ...rates });
    }
  });

  return { rows, errors, totalErrors };
}
