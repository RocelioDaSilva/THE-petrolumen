export interface PVTComponent {
  name: string;
  molecularWeight: number;
  criticalPressure: number;
  criticalTemperature: number;
  acentricFactor: number;
  criticalVolume: number;
  parachor: number;
  moleFraction: number;
}

export type PVTModelType = "black_oil" | "compositional";

export interface PVTModelSummary {
  id: string;
  name: string;
  type: PVTModelType;
  createdAt: string;
}

export interface SavedPVTModel extends PVTModelSummary {
  components: PVTComponent[];
}
