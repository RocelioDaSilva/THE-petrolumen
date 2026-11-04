const tools = [
  {
    id: "pvt",
    group: "PVT",
    title: "PVT EOS",
    endpoint: "/api/engine/pvt/eos",
    chartMode: "chart",
    fields: [
      { name: "pressure", type: "number", label: "Pressure (Pa)", value: 58_600_000, step: "any" },
      { name: "temperature", type: "number", label: "Temperature (K)", value: 433, step: "any" },
      {
        name: "components",
        type: "json",
        label: "Components · EosComponentInput[]",
        value: [
          { name: "C1", critical_pressure: 4_599_000, critical_temperature: 190.56, acentric_factor: 0.011, molecular_weight: 16.043 },
          { name: "C3", critical_pressure: 4_248_000, critical_temperature: 369.83, acentric_factor: 0.152, molecular_weight: 44.1 }
        ]
      },
      { name: "composition", type: "json", label: "Composition · object<string, number>", value: { C1: 0.85, C3: 0.15 } },
      { name: "eos_type", type: "select", label: "EOS type · Literal['PR']", value: "PR", options: ["PR"] },
      { name: "binary_interactions", type: "json", label: "Binary interactions · number[][] (optional)", value: null, optional: true }
    ]
  },
  {
    id: "trajectory",
    group: "DRILLING",
    title: "Drilling Trajectory",
    endpoint: "/api/engine/drilling/trajectory",
    chartMode: "chart",
    fields: [
      { name: "survey", type: "json", label: "Survey · object<string, number>[]", value: [{ md: 0, inc: 0, azi: 0 }, { md: 500, inc: 18, azi: 8 }, { md: 1000, inc: 32, azi: 18 }, { md: 1500, inc: 48, azi: 29 }, { md: 2000, inc: 65, azi: 45 }] },
      { name: "md_col", type: "text", label: "Measured-depth column", value: "md" },
      { name: "inc_col", type: "text", label: "Inclination column", value: "inc" },
      { name: "azi_col", type: "text", label: "Azimuth column", value: "azi" }
    ]
  },
  {
    id: "grid",
    group: "GEOLOGY",
    title: "Geology Grid",
    endpoint: "/api/engine/geology/grid",
    chartMode: "chart",
    fields: [
      { name: "nx", type: "number", label: "Nx · integer > 0", value: 50, step: 1 },
      { name: "ny", type: "number", label: "Ny · integer > 0", value: 50, step: 1 },
      { name: "nz", type: "number", label: "Nz · integer > 0", value: 20, step: 1 },
      { name: "dx", type: "json", label: "Dx · positive number or number[]", value: 25 },
      { name: "dy", type: "json", label: "Dy · positive number or number[]", value: 25 },
      { name: "dz", type: "json", label: "Dz · positive number or number[]", value: 5 }
    ]
  },
  {
    id: "nodal",
    group: "RESERVOIR",
    title: "Reservoir Nodal",
    endpoint: "/api/engine/reservoir/nodal",
    chartMode: "chart",
    fields: [
      { name: "qi", type: "number", label: "Qi · positive", value: 12000, step: "any" },
      { name: "pr", type: "number", label: "Pr · positive", value: 4200, step: "any" },
      { name: "p_surf", type: "number", label: "Surface pressure", value: 800, step: "any" },
      { name: "a", type: "number", label: "IPR coefficient a", value: 0.0015, step: "any" },
      { name: "b", type: "number", label: "IPR coefficient b", value: 8, step: "any" }
    ]
  },
  {
    id: "las-parse",
    group: "PETROPHYSICS",
    title: "LAS Parse",
    endpoint: "/api/petrophysics/las/parse",
    chartMode: null,
    isUpload: true,
    fields: [
      { name: "file", type: "file", label: "LAS File (.las)", accept: ".las" }
    ]
  },
  {
    id: "economics",
    group: "PRODUCTION",
    title: "Production Economics",
    endpoint: "/api/engine/production/economics",
    chartMode: null,
    fields: [
      { name: "oil_price", type: "number", label: "Oil price ($/bbl)", value: 70.0, step: "any" },
      { name: "gas_price", type: "number", label: "Gas price ($/Mscf)", value: 3.0, step: "any" },
      { name: "discount_rate", type: "number", label: "Discount rate (%)", value: 10.0, step: "any" },
      { name: "project_life", type: "number", label: "Project life (years)", value: 5, step: 1 },
      { name: "capex", type: "json", label: "CAPEX breakdown · object<string, number>", value: { drilling: 1000000, facilities: 500000 } },
      { name: "opex", type: "json", label: "Annual OPEX breakdown · object<string, number>", value: { fixed_opex: 50000, variable_opex: 25000 } },
      { name: "tax_rate", type: "number", label: "Tax rate (fraction 0-1)", value: 0.34, step: "any" },
      { name: "water_disposal_cost_per_bbl", type: "number", label: "Water disposal cost ($/bbl)", value: 1.5, step: "any" },
      { name: "oil_production", type: "json", label: "Annual oil production (bbl/yr) · number[]", value: [100000, 80000, 60000, 45000, 30000] },
      { name: "gas_production", type: "json", label: "Annual gas production (Mscf/yr) · number[]", value: [500000, 400000, 300000, 200000, 100000] },
      { name: "water_production", type: "json", label: "Annual water production (bbl/yr) · number[]", value: [20000, 30000, 40000, 50000, 60000] }
    ]
  },
  {
    id: "facies",
    group: "PETROPHYSICS",
    title: "Facies Classification",
    endpoint: "/api/engine/petrophysics/facies/classify",
    chartMode: null,
    fields: [
      {
        name: "predict_data",
        type: "json",
        label: "Predict log intervals · FaciesLogRecord[]",
        value: [
          { gamma: 38.0, resistivity: 135.0, density: 2.64, porosity: 0.10, depth: 2100.0 },
          { gamma: 68.0, resistivity: 42.0, density: 2.53, porosity: 0.17, depth: 2101.0 },
          { gamma: 125.0, resistivity: 5.2, density: 2.38, porosity: 0.24, depth: 2102.0 },
          { gamma: 22.0, resistivity: 240.0, density: 2.70, porosity: 0.06, depth: 2103.0 }
        ]
      },
      {
        name: "training_data",
        type: "json",
        label: "Custom training data (optional) · LabeledFaciesLogRecord[]",
        value: null,
        optional: true
      },
      { name: "n_estimators", type: "number", label: "Random Forest estimators", value: 100, step: 1 }
    ]
  },
  {
    id: "mbal",
    group: "PVT",
    title: "PVT Material Balance",
    endpoint: "/api/engine/pvt/mbal",
    chartMode: null,
    fields: [
      { name: "reservoir_type", type: "select", label: "Reservoir fluid type", value: "gas", options: ["oil", "gas"] },
      { name: "pressure_history", type: "json", label: "Pressure history (psia) · number[]", value: [4000.0, 3200.0] },
      {
        name: "production_history",
        type: "json",
        label: "Production history · ProductionPointInput[]",
        value: [{ oil_prod: 0.0, gas_prod: 5000000.0, water_prod: 100.0 }]
      },
      {
        name: "pvt_data",
        type: "json",
        label: "PVT table data (optional) · PvtPointInput[]",
        value: [
          { pressure: 3200.0, bo: 1.0, bg: 0.0011, rs: 0.0, z: 0.84 },
          { pressure: 4000.0, bo: 1.0, bg: 0.00082, rs: 0.0, z: 0.89 }
        ],
        optional: true
      },
      { name: "m", type: "number", label: "Gas cap ratio m", value: 0.0, step: "any" },
      { name: "We", type: "number", label: "Water influx We (bbl)", value: 500.0, step: "any" },
      { name: "Wp", type: "number", label: "Water production Wp (STB)", value: 100.0, step: "any" },
      { name: "Gp", type: "number", label: "Gas production Gp (Mscf)", value: 0.0, step: "any" },
      { name: "Bw", type: "number", label: "Water FVF Bw", value: 1.0, step: "any" },
      { name: "cw", type: "number", label: "Water compressibility cw (1/psi)", value: 3.0e-6, step: "any" },
      { name: "cf", type: "number", label: "Rock compressibility cf (1/psi)", value: 3.0e-6, step: "any" },
      { name: "Swi", type: "number", label: "Connate water saturation Swi", value: 0.2, step: "any" }
    ]
  },
  {
    id: "black-oil",
    group: "SIMULATION",
    title: "Simulate Black-Oil",
    endpoint: "/api/simulate/black-oil",
    chartMode: null,
    fields: [
      { name: "grid", type: "json", label: "Grid · GridInput", value: { nx: 2, ny: 2, nz: 1, dx: 50, dy: 50, dz: 10 } },
      { name: "porosity", type: "json", label: "Porosity · number[] (length nx*ny*nz)", value: [0.2, 0.2, 0.2, 0.2] },
      { name: "permeability", type: "json", label: "Permeability · number[] (length nx*ny*nz)", value: [100, 100, 100, 100] },
      { name: "rock_compressibility", type: "number", label: "Rock compressibility (>= 0)", value: 0, step: "any" },
      { name: "fluid_properties", type: "json", label: "Fluid properties · object<string, positive number>", value: { water_viscosity: 1, oil_viscosity: 2, gas_viscosity: 0.02 } },
      { name: "initial_pressure", type: "number", label: "Initial pressure (Pa) · positive", value: 3000, step: "any" },
      { name: "initial_water_saturation", type: "json", label: "Initial water saturation · number[] (0-1)", value: [0.2, 0.2, 0.2, 0.2] },
      { name: "initial_gas_saturation", type: "json", label: "Initial gas saturation · number[] (0-1)", value: [0, 0, 0, 0] },
      { name: "wells", type: "json", label: "Wells · WellInput[] (optional)", value: [] },
      { name: "timesteps", type: "json", label: "Timesteps · positive number[]", value: [1] }
    ]
  },
  {
    id: "compositional",
    group: "SIMULATION",
    title: "Simulate Compositional",
    endpoint: "/api/simulate/compositional",
    disabled: true,
    disabledNote: "Solver not implemented on backend (endpoint /api/simulate/compositional returns 501 Not Implemented).",
    fields: [
      { name: "grid", type: "json", label: "Grid · GridInput", value: { nx: 1, ny: 1, nz: 1, dx: 50, dy: 50, dz: 10 } },
      { name: "components", type: "json", label: "Components · ComponentInput[]", value: [{ name: "methane", mw: 16.043, tc: 190.56, pc: 4599000, omega: 0.011 }] },
      { name: "rock_properties", type: "json", label: "Rock properties · object<string, number>", value: {} },
      { name: "wells", type: "json", label: "Wells · object[]", value: [] },
      { name: "initial_composition", type: "json", label: "Initial composition · object<string, number>", value: { methane: 1 } },
      { name: "timesteps", type: "json", label: "Timesteps · positive number[]", value: [1] }
    ]
  },
  {
    id: "thermal",
    group: "SIMULATION",
    title: "Simulate Thermal",
    endpoint: "/api/simulate/thermal",
    disabled: true,
    disabledNote: "Solver not implemented on backend (endpoint /api/simulate/thermal returns 501 Not Implemented).",
    fields: [
      { name: "grid", type: "json", label: "Grid · GridInput", value: { nx: 1, ny: 1, nz: 1, dx: 50, dy: 50, dz: 10 } },
      { name: "components", type: "json", label: "Components · ComponentInput[]", value: [{ name: "methane", mw: 16.043, tc: 190.56, pc: 4599000, omega: 0.011 }] },
      { name: "rock_properties", type: "json", label: "Rock properties · object<string, number>", value: {} },
      { name: "wells", type: "json", label: "Wells · object[]", value: [] },
      { name: "initial_composition", type: "json", label: "Initial composition · object<string, number>", value: { methane: 1 } },
      { name: "timesteps", type: "json", label: "Timesteps · positive number[]", value: [1] },
      { name: "thermal_properties", type: "json", label: "Thermal properties · ThermalPropertiesInput", value: { rock_heat_capacity: 900, thermal_conductivity: 2, fluid_heat_capacity: 4200 } },
      { name: "initial_temperature", type: "number", label: "Initial temperature · positive", value: 350, step: "any" }
    ]
  }
];