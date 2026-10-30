/**
 * LAS 2.0 & Geophysical Well Log File Parser
 * Supports CWLS LAS (Log ASCII Standard) 2.0 / 3.0 and CSV/TSV table exports.
 */

export interface ParsedWellLogData {
  fileName: string;
  wellName?: string;
  startDepth: number;
  stopDepth: number;
  step: number;
  curves: string[];
  sampleCount: number;
  points: {
    depth: number;
    gr: number;
    res: number;
    rhob: number;
    nphi: number;
  }[];
}

export function parseLASContent(content: string, fileName: string): ParsedWellLogData {
  const lines = content.split(/\r?\n/).map((l) => l.trim());

  let inAsciiSection = false;
  let wellName = fileName.replace(/\.[^/.]+$/, "");
  const curves: string[] = [];
  const points: { depth: number; gr: number; res: number; rhob: number; nphi: number }[] = [];

  // Check if CSV format
  if (fileName.toLowerCase().endsWith(".csv") || lines[0]?.includes(",")) {
    return parseCSVContent(content, fileName);
  }

  // Parse LAS format
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line || line.startsWith("#")) continue;

    if (line.startsWith("~A") || line.startsWith("~ASCII")) {
      inAsciiSection = true;
      continue;
    }

    if (line.startsWith("~")) {
      inAsciiSection = false;
      continue;
    }

    if (!inAsciiSection) {
      if (/WELL\s*\./i.test(line)) {
        const match = line.match(/WELL\s*\.\s*([^:]+):/i) || line.match(/WELL\s*\.[^:]*:\s*([^:\r\n#]+)/i);
        if (match && match[1]) {
          const val = match[1].trim();
          if (val) wellName = val;
        }
      }
      continue;
    }

    // Inside ASCII data section
    const tokens = line.split(/\s+/).filter(Boolean).map(Number);
    if (tokens.length >= 1 && !isNaN(tokens[0])) {
      const depth = tokens[0];
      const gr = tokens.length > 1 && !isNaN(tokens[1]) && tokens[1] > -990 ? tokens[1] : 65.0;
      const res = tokens.length > 2 && !isNaN(tokens[2]) && tokens[2] > -990 ? tokens[2] : 15.0;
      const rhob = tokens.length > 3 && !isNaN(tokens[3]) && tokens[3] > -990 ? tokens[3] : 2.45;
      const nphi = tokens.length > 4 && !isNaN(tokens[4]) && tokens[4] > -990 ? tokens[4] : 0.18;

      points.push({
        depth: Number(depth.toFixed(1)),
        gr: Number(gr.toFixed(1)),
        res: Number(res.toFixed(2)),
        rhob: Number(rhob.toFixed(2)),
        nphi: Number(nphi.toFixed(3)),
      });
    }
  }

  if (points.length === 0) {
    throw new Error(`Não foram encontrados dados numéricos válidos na seção ~A do arquivo LAS "${fileName}".`);
  }

  points.sort((a, b) => a.depth - b.depth);

  return {
    fileName,
    wellName,
    startDepth: points[0].depth,
    stopDepth: points[points.length - 1].depth,
    step: points.length > 1 ? Number((points[1].depth - points[0].depth).toFixed(2)) : 0.5,
    curves: ["DEPTH", "GR", "RES", "RHOB", "NPHI"],
    sampleCount: points.length,
    points,
  };
}

function parseCSVContent(content: string, fileName: string): ParsedWellLogData {
  const lines = content.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) {
    throw new Error("Arquivo CSV sem linhas de dados suficientes.");
  }

  const delimiter = lines[0].includes(";") ? ";" : lines[0].includes("\t") ? "\t" : ",";
  const header = lines[0].split(delimiter).map((h) => h.trim().toUpperCase());

  const depthIdx = header.findIndex((h) => h.includes("DEPTH") || h === "DEPT" || h === "MD");
  const grIdx = header.findIndex((h) => h.includes("GR") || h.includes("GAMMA"));
  const resIdx = header.findIndex((h) => h.includes("RES") || h.includes("ILD") || h.includes("RT"));
  const rhobIdx = header.findIndex((h) => h.includes("RHOB") || h.includes("DENS"));
  const nphiIdx = header.findIndex((h) => h.includes("NPHI") || h.includes("NEUT") || h.includes("POR"));

  const targetDepthIdx = depthIdx >= 0 ? depthIdx : 0;
  const points: { depth: number; gr: number; res: number; rhob: number; nphi: number }[] = [];

  for (let i = 1; i < lines.length; i++) {
    const tokens = lines[i].split(delimiter).map((t) => Number(t.trim()));
    const depth = tokens[targetDepthIdx];
    if (isNaN(depth)) continue;

    const gr = grIdx >= 0 && !isNaN(tokens[grIdx]) ? tokens[grIdx] : 60;
    const res = resIdx >= 0 && !isNaN(tokens[resIdx]) ? tokens[resIdx] : 20;
    const rhob = rhobIdx >= 0 && !isNaN(tokens[rhobIdx]) ? tokens[rhobIdx] : 2.40;
    const nphi = nphiIdx >= 0 && !isNaN(tokens[nphiIdx]) ? tokens[nphiIdx] : 0.18;

    points.push({
      depth: Number(depth.toFixed(1)),
      gr: Number(gr.toFixed(1)),
      res: Number(res.toFixed(2)),
      rhob: Number(rhob.toFixed(2)),
      nphi: Number(nphi.toFixed(3)),
    });
  }

  if (points.length === 0) {
    throw new Error(`Nenhum ponto válido pôde ser extraído do arquivo CSV "${fileName}".`);
  }

  points.sort((a, b) => a.depth - b.depth);

  return {
    fileName,
    wellName: fileName.replace(/\.[^/.]+$/, ""),
    startDepth: points[0].depth,
    stopDepth: points[points.length - 1].depth,
    step: points.length > 1 ? Number((points[1].depth - points[0].depth).toFixed(2)) : 1.0,
    curves: header,
    sampleCount: points.length,
    points,
  };
}

/**
 * Standard calibrated reference geological sequence (deterministic, no random variance).
 * Represents an offshore turbidite reservoir sequence:
 * 2800m - 2858m: Overburden Shale (High GR, low resistivity)
 * 2860m - 2910m: Clean Sandstone Oil Pay Zone (Low GR 28-36 API, High Resistivity 85-140 ohm.m, RHOB 2.22, NPHI 0.24)
 * 2912m - 2950m: Basal Marine Shale (High GR 95-115 API, low resistivity 2-3 ohm.m)
 */
export function getCalibratedSampleLog(): { depth: number; gr: number; res: number; rhob: number; nphi: number }[] {
  const points = [];
  for (let d = 2800; d <= 2950; d += 2) {
    let gr: number;
    let res: number;
    let rhob: number;
    let nphi: number;

    if (d < 2860) {
      // Overburden shale
      const trend = (d - 2800) / 60;
      gr = 95 + 15 * Math.sin(d * 0.4);
      res = 2.2 + 0.8 * Math.cos(d * 0.3);
      rhob = 2.56 + 0.05 * Math.sin(d * 0.2);
      nphi = 0.14 + 0.02 * Math.cos(d * 0.5);
    } else if (d <= 2910) {
      // Sandstone Pay Zone (turbidite channel sand)
      const payFrac = (d - 2860) / 50;
      gr = 28 + 8 * Math.sin(payFrac * Math.PI);
      res = 85 + 55 * Math.sin(payFrac * Math.PI);
      rhob = 2.22 + 0.04 * Math.cos(payFrac * Math.PI * 2);
      nphi = 0.24 + 0.03 * Math.sin(payFrac * Math.PI);
    } else {
      // Basal Shale
      gr = 105 + 18 * Math.cos(d * 0.35);
      res = 1.8 + 0.6 * Math.sin(d * 0.25);
      rhob = 2.60 + 0.06 * Math.sin(d * 0.15);
      nphi = 0.12 + 0.02 * Math.sin(d * 0.4);
    }

    points.push({
      depth: d,
      gr: Number(gr.toFixed(1)),
      res: Number(res.toFixed(1)),
      rhob: Number(rhob.toFixed(2)),
      nphi: Number(nphi.toFixed(3)),
    });
  }
  return points;
}
