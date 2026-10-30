/**
 * PetroLúmen Canonical Example Well Specification
 * Reconciles cross-module baseline constants (DEF-01 through DEF-12)
 * All views and calculation default states draw from this single source of truth.
 */

export const EXAMPLE_WELL = {
  // Fluid & Reservoir Thermodynamics
  reservoirPressure: 3500,     // psia (reconciled across PVT, Nodal, Simulation)
  temperature: 180,             // °F
  gasGravity: 0.70,             // Specific gravity (air = 1.0)
  gor: 600,                     // scf/STB (Gas-Oil Ratio)
  oilApi: 35,                   // °API gravity (rho_o = 0.8498 g/cm3)
  waterCut: 0.25,               // Fraction (25% BSW)
  bubblePointPressure: 2765.5,  // psia (Standing correlation at 180°F, 600 scf/STB, 35 API, 0.70 SG)

  // Reservoir Geophysics & Petrophysics
  simulationPermeability: 50,   // mD (effective horizontal permeability)
  simulationPorosity: 0.20,     // Fraction (20% porosity)
  simulationViscosity: 1.5,     // cP (oil in-situ viscosity)
  simulationBlockSize: 100,     // ft (grid block dx, dy)
  reservoirThickness: 40,       // ft (pay zone net thickness)
  drainageRadius: 1500,         // ft
  wellboreRadius: 0.354,        // ft (8.5" open hole equivalent)

  // Production & Operations
  productionRate: -500,         // STB/d (negative by reservoir simulation sign convention)
  flowingBottomholePressure: 1800, // psia
  casingShoeTvd: 4500,          // ft TVD
  totalDepthTvd: 9000,          // ft TVD
  mudWeight: 10.0,              // ppg nominal drilling fluid density

  // Economic Baseline
  discountRate: 0.10,           // 10% annual discount rate (decimal, always)
  oilPriceUsdPerBbl: 75.0,      // $/bbl
  gasPriceUsdPerMcf: 3.50,      // $/Mcf
  operatingCostUsdPerBbl: 12.0, // $/bbl
} as const;

export type ExampleWell = typeof EXAMPLE_WELL;

/**
 * Returns a fresh copy of the canonical default well parameters.
 */
export function getDefaultWell(): ExampleWell {
  return { ...EXAMPLE_WELL };
}
