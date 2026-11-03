const tools = [
  {
    id: "pvt",
    group: "PVT",
    title: "PVT EOS",
    endpoint: "/api/engine/pvt/eos",
    fields: [
      { name: "pressure", type: "number", label: "Pressure (Pa)", value: 5000000, step: "any" },
      { name: "temperature", type: "number", label: "Temperature (K)", value: 250, step: "any" },
      {
        name: "components",
        type: "json",
        label: "Components · EosComponentInput[]",
        value: [{ name: "methane", critical_pressure: 4599000, critical_temperature: 190.56, acentric_factor: 0.011, molecular_weight: 16.043 }]
      },
      { name: "composition", type: "json", label: "Composition · object<string, number>", value: { methane: 1 } },
      { name: "eos_type", type: "select", label: "EOS type · Literal['PR']", value: "PR", options: ["PR"] },
      { name: "binary_interactions", type: "json", label: "Binary interactions · number[][] (optional)", value: null, optional: true }
    ]
  },
  {
    id: "trajectory",
    group: "DRILLING",
    title: "Drilling Trajectory",
    endpoint: "/api/engine/drilling/trajectory",
    fields: [
      { name: "survey", type: "json", label: "Survey · object<string, number>[]", value: [{ md: 0, inc: 0, azi: 0 }, { md: 100, inc: 0, azi: 0 }] },
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
    fields: [
      { name: "nx", type: "number", label: "Nx · integer > 0", value: 2, step: 1 },
      { name: "ny", type: "number", label: "Ny · integer > 0", value: 2, step: 1 },
      { name: "nz", type: "number", label: "Nz · integer > 0", value: 1, step: 1 },
      { name: "dx", type: "json", label: "Dx · positive number or number[]", value: 50 },
      { name: "dy", type: "json", label: "Dy · positive number or number[]", value: 50 },
      { name: "dz", type: "json", label: "Dz · positive number or number[]", value: 10 }
    ]
  },
  {
    id: "nodal",
    group: "RESERVOIR",
    title: "Reservoir Nodal",
    endpoint: "/api/engine/reservoir/nodal",
    fields: [
      { name: "qi", type: "number", label: "Qi · positive", value: 5000, step: "any" },
      { name: "pr", type: "number", label: "Pr · positive", value: 3000, step: "any" },
      { name: "p_surf", type: "number", label: "Surface pressure", value: 1000, step: "any" },
      { name: "a", type: "number", label: "IPR coefficient a", value: 0.002, step: "any" },
      { name: "b", type: "number", label: "IPR coefficient b", value: 10, step: "any" }
    ]
  },
  {
    id: "black-oil",
    group: "SIMULATION",
    title: "Simulate Black-Oil",
    endpoint: "/api/simulate/black-oil",
    fields: [
      { name: "grid", type: "json", label: "Grid · GridInput", value: { nx: 2, ny: 2, nz: 1, dx: 50, dy: 50, dz: 10 } },
      { name: "porosity", type: "json", label: "Porosity · number[]", value: [0.2, 0.2, 0.2, 0.2] },
      { name: "permeability", type: "json", label: "Permeability · number[]", value: [100, 100, 100, 100] },
      { name: "rock_compressibility", type: "number", label: "Rock compressibility", value: 0, step: "any" },
      { name: "fluid_properties", type: "json", label: "Fluid properties · object<string, positive number>", value: { water_viscosity: 1, oil_viscosity: 2, gas_viscosity: 0.02 } },
      { name: "initial_pressure", type: "number", label: "Initial pressure · positive", value: 3000, step: "any" },
      { name: "initial_water_saturation", type: "json", label: "Initial water saturation · number[]", value: [0.2, 0.2, 0.2, 0.2] },
      { name: "initial_gas_saturation", type: "json", label: "Initial gas saturation · number[]", value: [0, 0, 0, 0] },
      { name: "wells", type: "json", label: "Wells · WellInput[]", value: [] },
      { name: "timesteps", type: "json", label: "Timesteps · positive number[]", value: [1] }
    ]
  },
  {
    id: "compositional",
    group: "SIMULATION",
    title: "Simulate Compositional",
    endpoint: "/api/simulate/compositional",
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

const nav = document.querySelector("#tool-nav");
const form = document.querySelector("#tool-form");
const result = document.querySelector("#result-output");
const runButton = document.querySelector("#run-button");
let selectedTool = tools[0];
let apiPort = window.API_PORT || null;

function showTool(tool) {
  selectedTool = tool;
  document.querySelector("#tool-group").textContent = tool.group;
  document.querySelector("#tool-title").textContent = tool.title;
  document.querySelector("#result-caption").textContent = `POST ${tool.endpoint}`;
  document.querySelector("#run-status").textContent = "";
  result.textContent = "Select Run calculation to submit this request.";
  nav.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tool === tool.id);
  });
  form.replaceChildren();

  for (const field of tool.fields) {
    const wrapper = document.createElement("label");
    wrapper.className = "field";
    wrapper.htmlFor = `field-${field.name}`;
    const caption = document.createElement("span");
    caption.textContent = field.label;
    wrapper.append(caption);

    let input;
    if (field.type === "json") {
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
}

function getFormData() {
  const data = {};
  for (const field of selectedTool.fields) {
    const input = form.elements.namedItem(field.name);
    if (field.optional && input.value.trim() === "") continue;
    if (input.dataset.valueType === "json") {
      try {
        data[field.name] = JSON.parse(input.value);
      } catch {
        throw new Error(`${field.name}: enter valid JSON.`);
      }
    } else if (field.type === "number") {
      data[field.name] = Number(input.value);
    } else {
      data[field.name] = input.value;
    }
  }
  return data;
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
  status.textContent = "";
  result.textContent = "";
  try {
    if (!apiPort) throw new Error("The local API port is not available yet.");
    const body = getFormData();
    const response = await fetch(`http://127.0.0.1:${apiPort}${selectedTool.endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const text = await response.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      payload = { detail: text };
    }
    result.textContent = JSON.stringify(payload, null, 2);
    status.textContent = response.ok ? `HTTP ${response.status}` : `HTTP ${response.status} · ${formatError(payload)}`;
    status.classList.toggle("error", !response.ok);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("error");
    result.textContent = "Request was not completed.";
  }
}

for (const tool of tools) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "nav-item";
  button.dataset.tool = tool.id;
  button.textContent = tool.title;
  button.addEventListener("click", () => showTool(tool));
  nav.append(button);
}

runButton.addEventListener("click", runTool);
showTool(selectedTool);

window.addEventListener("pywebviewready", async () => {
  try {
    apiPort = await window.pywebview.api.get_port();
    window.API_PORT = apiPort;
    document.querySelector("#connection-status").textContent = `Local API · 127.0.0.1:${apiPort}`;
  } catch (error) {
    document.querySelector("#connection-status").textContent = `API bridge unavailable: ${error.message}`;
  }
});
