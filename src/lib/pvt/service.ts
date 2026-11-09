import type { PVTComponent, SavedPVTModel } from "./types";

export const PVT_MODELS_STORAGE_KEY = "petrolumen:pvt-models";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPVTComponent(value: unknown): value is PVTComponent {
  if (!isRecord(value)) return false;
  return (
    typeof value.name === "string" &&
    [
      value.molecularWeight,
      value.criticalPressure,
      value.criticalTemperature,
      value.acentricFactor,
      value.criticalVolume,
      value.parachor,
      value.moleFraction,
    ].every((number) => typeof number === "number" && Number.isFinite(number))
  );
}

function isSavedPVTModel(value: unknown): value is SavedPVTModel {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === "string" &&
    value.id.length > 0 &&
    typeof value.name === "string" &&
    value.name.trim().length > 0 &&
    (value.type === "black_oil" || value.type === "compositional") &&
    typeof value.createdAt === "string" &&
    Array.isArray(value.components) &&
    value.components.every(isPVTComponent)
  );
}

export function getSavedPVTModels(
  storage: Storage = window.localStorage,
): SavedPVTModel[] {
  const serialized = storage.getItem(PVT_MODELS_STORAGE_KEY);
  if (serialized === null) return [];

  let parsed: unknown;
  try {
    parsed = JSON.parse(serialized);
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error("Saved PVT models contain invalid JSON.");
    }
    throw error;
  }

  if (!Array.isArray(parsed) || !parsed.every(isSavedPVTModel)) {
    throw new TypeError("Saved PVT models have an invalid data shape.");
  }
  return parsed;
}

export function savePVTModel(
  model: SavedPVTModel,
  storage: Storage = window.localStorage,
): SavedPVTModel[] {
  if (!isSavedPVTModel(model)) {
    throw new TypeError("Cannot save an invalid PVT model.");
  }
  const models = getSavedPVTModels(storage);
  const existingIndex = models.findIndex((saved) => saved.id === model.id);
  if (existingIndex === -1) models.push(model);
  else models[existingIndex] = model;
  storage.setItem(PVT_MODELS_STORAGE_KEY, JSON.stringify(models));
  return models;
}

export function deletePVTModel(
  modelId: string,
  storage: Storage = window.localStorage,
): boolean {
  const models = getSavedPVTModels(storage);
  const remaining = models.filter((model) => model.id !== modelId);
  if (remaining.length === models.length) return false;
  storage.setItem(PVT_MODELS_STORAGE_KEY, JSON.stringify(remaining));
  return true;
}
