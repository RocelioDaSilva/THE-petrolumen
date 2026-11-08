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
    id: "compressibility-rock",
    group: "RESERVOIR",
    title: "Rock Compressibility",
    endpoint: "/api/engine/reservoir/compressibility/rock",
    chartMode: null,
    description: "Estimate pore-volume compressibility from porosity. Porosity is a fraction; strict mode enforces the published correlation range.",
    fields: [
      { name: "phi", type: "number", label: "Porosity fraction · 0 < phi < 1", value: 0.2, step: "any" },
      { name: "rock_type", type: "select", label: "Rock type", value: "sandstone", options: ["sandstone", "limestone"] },
      { name: "strict", type: "checkbox", label: "Reject porosity outside the correlation range", value: false }
    ]
  },
  {
    id: "compressibility-gas",
    group: "RESERVOIR",
    title: "Gas Compressibility",
    endpoint: "/api/engine/reservoir/compressibility/gas",
    chartMode: null,
    description: "Compute gas isothermal compressibility from the local Hall-Yarborough Z curve. Pressure is psia, temperature is degF, and gas specific gravity is relative to air.",
    fields: [
      { name: "p_psia", type: "number", label: "Pressure (psia)", value: 2500, step: "any" },
      { name: "temperature_f", type: "number", label: "Temperature (degF)", value: 150, step: "any" },
      { name: "gas_sg", type: "number", label: "Gas specific gravity (air = 1)", value: 0.9, step: "any" },
      { name: "h_psi", type: "number", label: "Derivative step (psi, optional)", value: null, step: "any", optional: true }
    ]
  },
  {
    id: "compressibility-total",
    group: "RESERVOIR",
    title: "Total Compressibility",
    endpoint: "/api/engine/reservoir/compressibility/total",
    chartMode: null,
    description: "Combine fluid compressibilities with Newman's rock correlation: ct = cg·Sg + co·So + cw·Sw + cf. Enter saturations as fractions summing to 1.",
    fields: [
      { name: "p_psia", type: "number", label: "Pressure (psia)", value: 2500, step: "any" },
      { name: "temperature_f", type: "number", label: "Temperature (degF)", value: 150, step: "any" },
      { name: "gas_sg", type: "number", label: "Gas specific gravity (air = 1)", value: 0.9, step: "any" },
      { name: "phi", type: "number", label: "Porosity fraction · 0 < phi < 1", value: 0.2, step: "any" },
      { name: "rock_type", type: "select", label: "Rock type", value: "sandstone", options: ["sandstone", "limestone"] },
      { name: "strict_rock_range", type: "checkbox", label: "Reject porosity outside the correlation range", value: false },
      { name: "co_psi_inv", type: "number", label: "Oil compressibility (1/psi)", value: 1.0e-5, step: "any" },
      { name: "cw_psi_inv", type: "number", label: "Water compressibility (1/psi)", value: 3.0e-6, step: "any" },
      { name: "sg", type: "number", label: "Gas saturation · fraction", value: 0.1, step: "any" },
      { name: "so", type: "number", label: "Oil saturation · fraction", value: 0.7, step: "any" },
      { name: "sw", type: "number", label: "Water saturation · fraction", value: 0.2, step: "any" }
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
    id: "ooip",
    group: "WORKFLOW",
    title: "OOIP Calculator",
    endpoint: "/api/workflow/ooip/run",
    chartMode: null,
    isOOIPWorkflow: true,
    fields: [
      { name: "file", type: "file", label: "LAS File (.las)", accept: ".las" },
      { name: "area_acres", type: "number", label: "Area (acres)", value: 640, step: "any" },
      { name: "net_to_gross_cutoff", type: "number", label: "Porosity cutoff (0-1)", value: 0.1, step: "any" },
      { name: "a", type: "number", label: "Archie a", value: 1.0, step: "any" },
      { name: "m", type: "number", label: "Cementation exponent m", value: 2.0, step: "any" },
      { name: "n", type: "number", label: "Saturation exponent n", value: 2.0, step: "any" },
      { name: "Rw", type: "number", label: "Formation water resistivity Rw (ohm-m)", value: 0.1, step: "any" }
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
for (const tool of tools) {
  tool.defaultValues = {};
  for (const field of tool.fields) {
    tool.defaultValues[field.name] = field.value !== undefined ? JSON.parse(JSON.stringify(field.value)) : null;
  }
}

const nav = document.querySelector("#tool-nav");
const form = document.querySelector("#tool-form");
const result = document.querySelector("#result-output");
const runButton = document.querySelector("#run-button");
const resultModeButtons = document.querySelectorAll(".result-mode");
let selectedTool = tools[0];
let apiPort = window.API_PORT || null;
let currentResultMode = "chart";

function updateResultModeButtons() {
  const hasChartMode = selectedTool && !selectedTool.disabled && Boolean(selectedTool.chartMode);
  resultModeButtons.forEach((button) => {
    if (button.dataset.mode === "chart") {
      button.disabled = !hasChartMode;
      button.classList.toggle("mode-disabled", !hasChartMode);
      button.title = hasChartMode ? "View graphical chart" : "Chart view not available for this tool";
    }
    const active = button.dataset.mode === currentResultMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function renderOoipCard(payload) {
  const output = document.querySelector("#result-output");
  output.classList.remove("chart-output");
  output.classList.add("json-output");
  output.dataset.payload = JSON.stringify(payload ?? {});

  output.innerHTML = `
    <div class="ooip-card">
      <h3>OOIP Result</h3>
      <table>
        <tr><td>Net pay</td><td>${payload.net_pay_ft} ft</td></tr>
        <tr><td>Gross pay</td><td>${payload.gross_pay_ft} ft</td></tr>
        <tr><td>Net/Gross</td><td>${payload.net_to_gross}</td></tr>
        <tr><td>Average porosity</td><td>${payload.average_porosity}</td></tr>
        <tr><td>Average Sw</td><td>${payload.average_sw}</td></tr>
        <tr><td><strong>OOIP</strong></td><td><strong>${payload.ooip_bbl}</strong> bbl</td></tr>
        <tr><td>OOIP per acre-ft</td><td>${payload.ooip_stb_per_acre_ft} STB/ac-ft</td></tr>
      </table>
      <p class="ooip-note">${payload.note}</p>
    </div>
  `;
}

function renderCompressibilityCard(payload) {
  const output = document.querySelector("#result-output");
  output.classList.remove("chart-output");
  output.classList.add("json-output");
  output.dataset.payload = JSON.stringify(payload ?? {});

  const rows = selectedTool.id === "compressibility-rock"
    ? [
        ["Rock type", payload.rock_type],
        ["Pore-volume compressibility", formatCompressibility(payload.cf_psi_inv)],
        ["Within published porosity range", payload.in_validity_range ? "Yes" : "No"]
      ]
    : selectedTool.id === "compressibility-gas"
      ? [
          ["Gas compressibility", formatCompressibility(payload.cg_psi_inv)],
          ["Z-factor", formatScalar(payload.z_at_p)],
          ["dZ/dP", formatCompressibility(payload.dz_dp_psi_inv)],
          ["Derivative method", `${payload.method} difference, h = ${formatScalar(payload.h_psi)} psi`],
          ["Z correlation", payload.z_correlation]
        ]
      : [
          ["Total compressibility", formatCompressibility(payload.ct_psi_inv)],
          ["Gas compressibility", formatCompressibility(payload.cg_psi_inv)],
          ["Rock compressibility", formatCompressibility(payload.cf_psi_inv)],
          ["Z-factor", formatScalar(payload.z_at_p)],
          ["Within published rock range", payload.in_rock_validity_range ? "Yes" : "No"],
          ["Z correlation", payload.z_correlation]
        ];

  const card = document.createElement("div");
  card.className = "compressibility-card";
  const heading = document.createElement("h3");
  heading.textContent = "Reservoir Compressibility Result";
  card.append(heading);

  const table = document.createElement("table");
  for (const [label, value] of rows) {
    const row = table.insertRow();
    row.insertCell().textContent = label;
    row.insertCell().textContent = value ?? "—";
  }
  card.append(table);

  const note = document.createElement("p");
  note.className = "compressibility-note";
  note.textContent = "Use as a screening or learning calculation. Correlation validity and input units matter; confirm critical design values with appropriate laboratory data and engineering review.";
  card.append(note);
  output.replaceChildren(card);
}

function formatCompressibility(value) {
  return Number.isFinite(value) ? `${value.toExponential(4)} 1/psi` : "—";
}

function formatScalar(value) {
  return Number.isFinite(value) ? value.toPrecision(6) : "—";
}

function renderLasTable(payload) {
  const output = document.querySelector("#result-output");
  output.classList.remove("chart-output");
  output.classList.add("json-output");
  output.dataset.payload = JSON.stringify(payload ?? {});

  if (!payload || !payload.curves || !payload.curve_stats) {
    output.textContent = JSON.stringify(payload ?? {}, null, 2);
    return;
  }

  const container = document.createElement("div");
  const summary = document.createElement("div");
  summary.className = "las-summary";
  const wellName = payload.well?.WELL || payload.well?.well || "Unknown";
  const rowCount = payload.row_count ?? 0;
  const curveCount = payload.curves.length;
  summary.innerHTML = `Well: <span>${wellName}</span> | Curves: <span>${curveCount}</span> (${payload.curves.join(", ")}) | Rows: <span>${rowCount}</span>`;
  container.append(summary);

  const table = document.createElement("table");
  table.className = "las-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Curve Name</th>
        <th>Min</th>
        <th>Max</th>
        <th>Mean</th>
      </tr>
    </thead>
    <tbody>
      ${payload.curves.map((curve) => {
        const stats = payload.curve_stats[curve] || {};
        const minVal = stats.min !== null && stats.min !== undefined ? (typeof stats.min === "number" ? stats.min.toFixed(4) : stats.min) : "—";
        const maxVal = stats.max !== null && stats.max !== undefined ? (typeof stats.max === "number" ? stats.max.toFixed(4) : stats.max) : "—";
        const meanVal = stats.mean !== null && stats.mean !== undefined ? (typeof stats.mean === "number" ? stats.mean.toFixed(4) : stats.mean) : "—";
        return `
          <tr>
            <td><strong>${curve}</strong></td>
            <td>${minVal}</td>
            <td>${maxVal}</td>
            <td>${meanVal}</td>
          </tr>
        `;
      }).join("")}
    </tbody>
  `;
  container.append(table);
  output.replaceChildren(container);
}

function setResultDisplay(payload) {
  const output = document.querySelector("#result-output");
  output.classList.toggle("chart-output", currentResultMode === "chart");
  output.classList.toggle("json-output", currentResultMode !== "chart");
  output.dataset.payload = JSON.stringify(payload ?? {});

  if (selectedTool?.id === "las-parse" && payload && payload.curve_stats) {
    renderLasTable(payload);
    return;
  }

  if (selectedTool?.isOOIPWorkflow && payload && payload.ooip_bbl !== undefined) {
    renderOoipCard(payload);
    return;
  }

  if (selectedTool?.id.startsWith("compressibility-") && payload && Object.keys(payload).length > 0) {
    renderCompressibilityCard(payload);
    return;
  }

  if (currentResultMode === "chart") {
    if (payload && typeof payload.image_base64 === "string") {
      output.innerHTML = `<img src="data:${payload.content_type || "image/png"};base64,${payload.image_base64}" alt="Chart output" />`;
    } else {
      output.textContent = "No chart image was returned by the engine.";
    }
    return;
  }

  output.textContent = JSON.stringify(payload ?? {}, null, 2);
}

function showTool(tool) {
  selectedTool = tool;
  currentResultMode = tool.chartMode ? tool.chartMode : "json";
  document.querySelector("#tool-group").textContent = tool.group;
  document.querySelector("#tool-title").textContent = tool.title;
  document.querySelector("#tool-description").textContent =
    tool.description || "Values follow the backend request model.";
  document.querySelector("#result-caption").textContent = `POST ${tool.endpoint}`;
  document.querySelector("#run-status").textContent = "";
  setResultDisplay({});
  nav.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tool === tool.id);
  });
  form.replaceChildren();

  const formActions = document.querySelector(".form-actions");
  if (tool.disabled) {
    const notice = document.createElement("div");
    notice.className = "tool-disabled-notice";
    notice.innerHTML = `<strong>Tool Unavailable</strong><p>${tool.disabledNote}</p>`;
    form.append(notice);
    if (formActions && formActions.style) formActions.style.display = "none";
    runButton.disabled = true;
    runButton.textContent = "Unavailable";
    updateResultModeButtons();
    const resultOutput = document.querySelector("#result-output");
    resultOutput.classList.remove("chart-output");
    resultOutput.classList.add("json-output");
    resultOutput.textContent = `[DISABLED] ${tool.title}\n\nReason: ${tool.disabledNote}\nEndpoint: POST ${tool.endpoint}\nStatus: 501 Not Implemented`;
    return;
  }

  if (formActions && formActions.style) formActions.style.display = "flex";
  runButton.disabled = false;
  runButton.textContent = "Run calculation";
  updateResultModeButtons();

  for (const field of tool.fields) {
    const wrapper = document.createElement("label");
    wrapper.className = "field";
    wrapper.htmlFor = `field-${field.name}`;
    const caption = document.createElement("span");
    caption.textContent = field.label;
    wrapper.append(caption);

    let input;
    if (field.type === "file") {
      input = document.createElement("input");
      input.type = "file";
      if (field.accept) input.accept = field.accept;
    } else if (field.type === "checkbox") {
      input = document.createElement("input");
      input.type = "checkbox";
      input.checked = Boolean(field.value);
    } else if (field.type === "json") {
      input = document.createElement("textarea");
      input.rows = Array.isArray(field.value) ? 5 : 3;
      input.value = field.value === null ? "" : JSON.stringify(field.value, null, 2);
      input.dataset.valueType = "json";
    } else if (field.type === "select") {
      input = document.createElement("select");
      for (const option of field.options) {
        const element = document.createElement("option");
        element.value = option;
        element.textContent = option;
        input.append(element);
      }
      input.value = field.value;
    } else {
      input = document.createElement("input");
      input.type = field.type;
      input.value = field.value;
      if (field.step) input.step = field.step;
      if (field.type === "number") input.inputMode = "decimal";
    }
    input.id = `field-${field.name}`;
    input.name = field.name;
    if (field.optional) input.placeholder = "Optional — leave blank to omit";
    wrapper.append(input);
    form.append(wrapper);
  }

  if (!tool.isUpload && !tool.isOOIPWorkflow) {
    const resetButton = document.createElement("button");
    resetButton.type = "button";
    resetButton.className = "reset-button";
    resetButton.textContent = "Reset to example";
    resetButton.addEventListener("click", () => applyExampleValues(tool));
    form.append(resetButton);
  }
}

function applyExampleValues(tool) {
  for (const field of tool.fields) {
    const input = form.elements.namedItem(field.name);
    if (!input) continue;
    const value = tool.defaultValues[field.name];
    if (field.type === "json") {
      input.value = value === null ? "" : JSON.stringify(value, null, 2);
    } else if (field.type === "select") {
      input.value = value;
    } else if (field.type === "checkbox") {
      input.checked = Boolean(value);
    } else {
      input.value = value;
    }
  }
}

function getFormData() {
  const data = {};
  for (const field of selectedTool.fields) {
    const input = form.elements.namedItem(field.name);
    if (!input) continue;
    if (field.optional && input.value.trim() === "") continue;
    if (field.type === "checkbox") {
      data[field.name] = input.checked;
    } else if (input.dataset.valueType === "json") {
      try {
        data[field.name] = JSON.parse(input.value);
      } catch (err) {
        throw new Error(`${field.name}: enter valid JSON (${err.message}).`);
      }
    } else if (field.type === "number") {
      const num = Number(input.value);
      if (!Number.isFinite(num)) {
        throw new Error(`${field.name}: must be a finite number.`);
      }
      data[field.name] = num;
    } else {
      data[field.name] = input.value;
    }
  }

  // Pre-flight validation based on tool domain
  validateToolData(selectedTool.id, data);

  return data;
}

function validateToolData(toolId, data) {
  if (toolId === "black-oil") {
    if (!data.grid || typeof data.grid !== "object") {
      throw new Error("Grid configuration object is required.");
    }
    const { nx, ny, nz } = data.grid;
    if (!Number.isInteger(nx) || nx <= 0 || !Number.isInteger(ny) || ny <= 0 || !Number.isInteger(nz) || nz <= 0) {
      throw new Error("Grid nx, ny, nz must be positive integers.");
    }
    const cellCount = nx * ny * nz;
    if (cellCount > 512) {
      throw new Error(`Grid exceeds solver limit of 512 cells (nx*ny*nz = ${cellCount}). Reduce grid dimensions.`);
    }
    for (const arrName of ["porosity", "permeability", "initial_water_saturation", "initial_gas_saturation"]) {
      if (!Array.isArray(data[arrName])) {
        throw new Error(`${arrName} must be a JSON array.`);
      }
      if (data[arrName].length !== cellCount) {
        throw new Error(`${arrName} length (${data[arrName].length}) must match cell count (${cellCount}).`);
      }
    }
    for (let i = 0; i < cellCount; i++) {
      const sw = data.initial_water_saturation[i];
      const sg = data.initial_gas_saturation[i];
      if (sw < 0 || sw > 1 || sg < 0 || sg > 1) {
        throw new Error(`Saturations at cell ${i} must be between 0 and 1.`);
      }
      if (sw + sg > 1) {
        throw new Error(`Water and gas saturation at cell ${i} sum to > 1 (${sw + sg}).`);
      }
    }
  } else if (toolId === "pvt") {
    if (data.pressure <= 0 || data.temperature <= 0) {
      throw new Error("Pressure and temperature must be positive numbers.");
    }
    if (!Array.isArray(data.components) || data.components.length === 0) {
      throw new Error("Components array must not be empty.");
    }
    if (!data.composition || typeof data.composition !== "object") {
      throw new Error("Composition mapping is required.");
    }
    const fractions = Object.values(data.composition);
    const sumFractions = fractions.reduce((acc, val) => acc + val, 0);
    if (Math.abs(sumFractions - 1.0) > 1e-4) {
      throw new Error(`Mole fractions must sum to 1.0 (currently sums to ${sumFractions.toFixed(4)}).`);
    }
  } else if (toolId === "grid") {
    if (data.nx <= 0 || data.ny <= 0 || data.nz <= 0) {
      throw new Error("nx, ny, nz must be positive integers.");
    }
  } else if (toolId === "nodal") {
    if (data.qi <= 0 || data.pr <= 0) {
      throw new Error("qi and pr must be positive numbers.");
    }
    if (data.p_surf < 0 || data.a < 0 || data.b < 0) {
      throw new Error("p_surf, a, and b must be non-negative.");
    }
  }
}

function formatError(body) {
  if (Array.isArray(body?.detail)) {
    return body.detail.map((issue) => {
      const field = Array.isArray(issue.loc) ? issue.loc.slice(1).join(".") : "request";
      return `${field || "request"}: ${issue.msg || "invalid value"}`;
    }).join("\n");
  }
  return typeof body?.detail === "string" ? body.detail : JSON.stringify(body, null, 2);
}

async function runTool() {
  const status = document.querySelector("#run-status");
  const timing = document.querySelector("#response-time");
  timing.textContent = "Response time: —";
  status.textContent = "";
  try {
    if (!apiPort) throw new Error("The local API port is not available yet.");

    let response;
    const started = performance.now();

    if (selectedTool.isOOIPWorkflow) {
      const fileInput = form.elements.namedItem("file");
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        throw new Error("Please select a .las file.");
      }
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      const uploadResponse = await fetch(`http://127.0.0.1:${apiPort}/api/workflow/ooip/upload`, {
        method: "POST",
        body: formData
      });

      const uploadText = await uploadResponse.text();
      let uploadPayload;
      try {
        uploadPayload = uploadText ? JSON.parse(uploadText) : {};
      } catch {
        uploadPayload = { detail: uploadText };
      }

      if (!uploadResponse.ok) {
        status.textContent = `HTTP ${uploadResponse.status} · ${formatError(uploadPayload)}`;
        status.classList.add("error");
        document.querySelector("#result-output").textContent = "Request was not completed.";
        return;
      }

      const sessionId = uploadPayload.session_id;
      const areaAcres = Number(form.elements.namedItem("area_acres")?.value ?? 640);
      const netToGrossCutoff = Number(form.elements.namedItem("net_to_gross_cutoff")?.value ?? 0.1);
      const a = Number(form.elements.namedItem("a")?.value ?? 1.0);
      const m = Number(form.elements.namedItem("m")?.value ?? 2.0);
      const n = Number(form.elements.namedItem("n")?.value ?? 2.0);
      const rw = Number(form.elements.namedItem("Rw")?.value ?? 0.1);

      const runPayload = {
        session_id: sessionId,
        area_acres: areaAcres,
        net_to_gross_cutoff: netToGrossCutoff,
        water_saturation_method: "archie",
        archie_params: { a, m, n, Rw: rw }
      };

      response = await fetch(`http://127.0.0.1:${apiPort}${selectedTool.endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(runPayload)
      });
    } else if (selectedTool.isUpload) {
      const fileInput = form.elements.namedItem("file");
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        throw new Error("Please select a .las file to upload.");
      }
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      response = await fetch(`http://127.0.0.1:${apiPort}${selectedTool.endpoint}`, {
        method: "POST",
        body: formData
      });
    } else {
      const body = getFormData();
      const endpoint = currentResultMode === "chart" && selectedTool.chartMode ? `${selectedTool.endpoint}/chart` : selectedTool.endpoint;
      response = await fetch(`http://127.0.0.1:${apiPort}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
    }

    const elapsedMs = Math.round(performance.now() - started);
    const text = await response.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      payload = { detail: text };
    }
    setResultDisplay(payload);
    timing.textContent = `Response time: ${elapsedMs}ms`;
    status.textContent = response.ok ? `HTTP ${response.status}` : `HTTP ${response.status} · ${formatError(payload)}`;
    status.classList.toggle("error", !response.ok);
  } catch (error) {
    timing.textContent = "Response time: —";
    status.textContent = error.message;
    status.classList.add("error");
    document.querySelector("#result-output").textContent = "Request was not completed.";
  }
}

function renderSidebarNav() {
  nav.replaceChildren();

  const activeTools = tools.filter((tool) => !tool.disabled);
  const disabledTools = tools.filter((tool) => tool.disabled);

  activeTools.forEach((tool) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "nav-item";
    button.dataset.tool = tool.id;
    button.textContent = tool.title;
    button.addEventListener("click", () => showTool(tool));
    nav.append(button);
  });

  if (disabledTools.length > 0) {
    const divider = document.createElement("div");
    divider.className = "nav-section-title";
    divider.textContent = "UPCOMING SOLVERS";
    nav.append(divider);

    disabledTools.forEach((tool) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "nav-item disabled";
      button.dataset.tool = tool.id;
      button.textContent = `${tool.title} (501)`;
      button.setAttribute("aria-disabled", "true");
      button.title = tool.disabledNote;
      button.addEventListener("click", () => showTool(tool));
      nav.append(button);
    });
  }
}

renderSidebarNav();

resultModeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentResultMode = button.dataset.mode;
    updateResultModeButtons();
    const activePayload = document.querySelector("#result-output").dataset.payload ? JSON.parse(document.querySelector("#result-output").dataset.payload) : {};
    setResultDisplay(activePayload);
    if (selectedTool && !selectedTool.disabled) {
      document.querySelector("#result-caption").textContent = `POST ${selectedTool.endpoint}`;
    }
  });
});

runButton.addEventListener("click", runTool);
showTool(selectedTool);

async function checkApiHealth() {
  const dot = document.querySelector("#footer-status-dot");
  const statusText = document.querySelector("#connection-status");
  const port = apiPort || 8000;
  const url = `http://127.0.0.1:${port}/health`;

  try {
    const response = await fetch(url, { method: "GET" });
    if (response.ok) {
      const data = await response.json();
      if (dot) {
        dot.className = "status-dot online";
      }
      if (statusText) {
        statusText.textContent = `Online · 127.0.0.1:${port} (v${data.version || "0.1.0"})`;
      }
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    if (dot) {
      dot.className = "status-dot offline";
    }
    if (statusText) {
      statusText.textContent = `API Offline (${error.message || "Failed to fetch"})`;
    }
  }
}

window.addEventListener("pywebviewready", async () => {
  try {
    apiPort = await window.pywebview.api.get_port();
    window.API_PORT = apiPort;
    checkApiHealth();
  } catch (error) {
    const dot = document.querySelector("#footer-status-dot");
    if (dot) dot.className = "status-dot offline";
    document.querySelector("#connection-status").textContent = `API bridge unavailable: ${error.message}`;
  }
});

// Run initial health check on page load as well
window.addEventListener("DOMContentLoaded", () => {
  checkApiHealth();
});
// If DOM is already loaded
if (document.readyState === "complete" || document.readyState === "interactive") {
  checkApiHealth();
}
