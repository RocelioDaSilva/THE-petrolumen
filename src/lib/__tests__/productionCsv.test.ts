import { describe, expect, it } from "vitest";
import { parseProductionCsv } from "../productionCsv";

describe("parseProductionCsv", () => {
  it("parses UTF-8 BOM headers, quoted well names, and blank optional rates", () => {
    const result = parseProductionCsv(
      "\uFEFFwell_name,date,oil_rate,gas_rate,water_rate\r\n" +
        '"Well, North",2025-01-31,10.5,,2\r\n',
    );

    expect(result).toEqual({
      rows: [
        {
          well_name: "Well, North",
          date: "2025-01-31",
          oil_rate: 10.5,
          gas_rate: null,
          water_rate: 2,
        },
      ],
      errors: [],
      totalErrors: 0,
    });
  });

  it("reports invalid dates, non-finite rates, and rows with no rate values", () => {
    const result = parseProductionCsv(
      "well_name,date,oil_rate,gas_rate\n" +
        "Well A,2025-02-30,10,\n" +
        "Well B,2025-01-01,Infinity,\n" +
        "Well C,2025-01-02,,\n",
    );

    expect(result.rows).toHaveLength(0);
    expect(result.errors.map((error) => error.row)).toEqual([2, 3, 3, 4]);
    expect(result.totalErrors).toBe(4);
  });

  it("rejects CSV files with missing required columns", () => {
    const result = parseProductionCsv("well_name,oil_rate\nWell A,2\n");

    expect(result.rows).toEqual([]);
    expect(result.errors[0].message).toContain("date");
  });

  it("reports malformed quoting instead of returning a partial preview", () => {
    const result = parseProductionCsv(
      'well_name,date,oil_rate\n"Well A,2025-01-01,2\n',
    );

    expect(result.rows).toEqual([]);
    expect(result.errors[0].message).toContain("unterminated");
  });
});
