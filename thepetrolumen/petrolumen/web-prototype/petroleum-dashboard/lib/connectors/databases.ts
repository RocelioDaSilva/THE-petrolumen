// Stub para uso em DeclineCurveAnalysis
export function generateProductionData() {
  // Retorna dados mockados para o gráfico
  return [
    { date: '2022-01-01', oil: 100, gas: 50, water: 10 },
    { date: '2022-02-01', oil: 90, gas: 48, water: 12 },
    { date: '2022-03-01', oil: 80, gas: 45, water: 15 },
  ];
}

// Função exportada para uso em ReservoirVisualization3D
export function generateReservoirProperties() {
  // Gera propriedades mockadas para visualização 3D
  const gridSize = { nx: 50, ny: 50, nz: 10 };
  const properties = [];
  for (let i = 0; i < 100; i++) {
    const x = Math.floor(Math.random() * gridSize.nx);
    const y = Math.floor(Math.random() * gridSize.ny);
    const z = Math.floor(Math.random() * gridSize.nz);
    properties.push({
      block_id: `${x},${y},${z}`,
      porosity: 0.1 + Math.random() * 0.2,
      permeability_x: 10 + Math.random() * 990,
      permeability_y: 10 + Math.random() * 990,
      permeability_z: 1 + Math.random() * 99,
      net_to_gross: 0.7 + Math.random() * 0.3,
      water_saturation: 0.2 + Math.random() * 0.3,
      pressure: 3000 + Math.random() * 2000,
      temperature: 150 + Math.random() * 100,
    });
  }
  return {
    metadata: {
      gridSize: gridSize,
      count: properties.length,
    },
    properties: properties,
  };
}
import type { DatabaseConfig, DatabaseType, DataQuery } from "./types"

// Mock implementation of database connectors
// In a real implementation, this would connect to actual databases

class DatabaseConnector {
  private config: DatabaseConfig
  private activeQueries: Map<string, DataQuery> = new Map()

  constructor(config: DatabaseConfig) {
    this.config = config
  }

  async connect(): Promise<boolean> {
    console.log(
      `Connecting to ${this.config.type} database at ${this.config.host}:${this.config.port}/${this.config.database}`,
    )

    try {
      // In a real implementation, this would:
      // 1. Establish a connection to the database
      // 2. Verify credentials
      // 3. Test a simple query

      // Simulate connection delay
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Update connection status
      this.config.status = {
        connected: true,
        lastConnected: new Date(),
        version: this.getDatabaseVersion(this.config.type),
      }

      return true
    } catch (error) {
      this.config.status = {
        connected: false,
        error: error instanceof Error ? error.message : String(error),
      }
      return false
    }
  }

  async disconnect(): Promise<boolean> {
    // Cancel any running queries
    for (const [queryId, query] of this.activeQueries.entries()) {
      if (query.status === "running") {
        await this.cancelQuery(queryId)
      }
    }

    this.config.status.connected = false
    return true
  }

  async executeQuery(queryData: Omit<DataQuery, "id" | "status" | "createdAt" | "updatedAt">): Promise<DataQuery> {
    if (!this.config.status.connected) {
      throw new Error(`Database ${this.config.name} is not connected`)
    }

    const queryId = `query-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`

    const newQuery: DataQuery = {
      id: queryId,
      sourceId: this.config.id,
      query: queryData.query,
      parameters: queryData.parameters,
      status: "pending",
      createdAt: new Date(),
      updatedAt: new Date(),
    }

    this.activeQueries.set(queryId, newQuery)

    // Simulate query execution in background
    this.runQuery(queryId)

    return newQuery
  }

  async getQueryStatus(queryId: string): Promise<DataQuery> {
    const query = this.activeQueries.get(queryId)
    if (!query) {
      throw new Error(`Query ${queryId} not found`)
    }
    return query
  }

  async cancelQuery(queryId: string): Promise<DataQuery> {
    const query = this.activeQueries.get(queryId)
    if (!query) {
      throw new Error(`Query ${queryId} not found`)
    }

    if (query.status === "running") {
      query.status = "failed"
      query.error = "Query canceled by user"
      query.updatedAt = new Date()
    }

    return query
  }

  getConfig(): DatabaseConfig {
    return this.config
  }

  private async runQuery(queryId: string): Promise<void> {
    const query = this.activeQueries.get(queryId)
    if (!query) return

    // Update query status to running
    query.status = "running"
    query.updatedAt = new Date()

    // Simulate query execution time
    const executionTime = Math.floor(Math.random() * 2000) + 500 // 500-2500ms
    await new Promise((resolve) => setTimeout(resolve, executionTime))

    try {
      // Generate mock results based on query
      query.results = this.generateMockResults(query)
      query.status = "completed"
      query.executionTime = executionTime
    } catch (error) {
      query.status = "failed"
      query.error = error instanceof Error ? error.message : String(error)
    }

    query.updatedAt = new Date()
  }

  private generateMockResults(query: DataQuery): any {
    // Extract query type from the SQL or other query language
    const queryText = query.query.toLowerCase()

    // Check if it's a production data query
    if (queryText.includes("production") || queryText.includes("well_data")) {
      return this.generateProductionData()
    }

    // Check if it's a well data query
    if (queryText.includes("well") || queryText.includes("completion")) {
      return this.generateWellData()
    }

    // Check if it's a reservoir property query
    if (queryText.includes("reservoir") || queryText.includes("property") || queryText.includes("petrophysical")) {
      return this.generateReservoirProperties()
    }

    // Check if it's a PVT data query
    if (queryText.includes("pvt") || queryText.includes("fluid")) {
      return this.generatePVTData()
    }

    // Default to a generic result
    return {
      metadata: {
        columns: ["id", "name", "value", "unit", "timestamp"],
        types: ["integer", "string", "float", "string", "datetime"],
      },
      rows: Array.from({ length: 10 }, (_, i) => [
        i + 1,
        `Item ${i + 1}`,
        Math.random() * 100,
        ["psi", "bbl", "scf", "ft"][Math.floor(Math.random() * 4)],
        new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      ]),
    }
  }

  private generateProductionData() {
    const wells = ["WELL-001", "WELL-002", "WELL-003", "WELL-004", "WELL-005"]
    const startDate = new Date(2022, 0, 1)
    const endDate = new Date(2023, 0, 1)
    const daysDiff = Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))

    const data = []

    for (const well of wells) {
      // Base production values
      let oilRate = 1000 + Math.random() * 500 // 1000-1500 bbl/d
      let gasRate = 1.2e6 + Math.random() * 0.5e6 // 1.2-1.7 MMscf/d
      let waterRate = 200 + Math.random() * 300 // 200-500 bbl/d

      // Decline rates
      const oilDecline = 0.1 + Math.random() * 0.1 // 10-20% annual decline
      const gasDecline = 0.05 + Math.random() * 0.15 // 5-20% annual decline
      const waterIncline = 0.2 + Math.random() * 0.3 // 20-50% annual incline

      // Generate daily data
      for (let day = 0; day < daysDiff; day += 7) {
        // Weekly data points
        const currentDate = new Date(startDate)
        currentDate.setDate(startDate.getDate() + day)

        // Apply decline/incline
        const yearFraction = day / 365
        oilRate *= Math.pow(1 - oilDecline, yearFraction)
        gasRate *= Math.pow(1 - gasDecline, yearFraction)
        waterRate *= Math.pow(1 + waterIncline, yearFraction)

        // Add some noise
        const oilNoise = 1 + (Math.random() * 0.1 - 0.05) // ±5%
        const gasNoise = 1 + (Math.random() * 0.1 - 0.05) // ±5%
        const waterNoise = 1 + (Math.random() * 0.15 - 0.075) // ±7.5%

        data.push({
          well: well,
          date: currentDate.toISOString().split("T")[0],
          oil_rate: oilRate * oilNoise,
          gas_rate: gasRate * gasNoise,
          water_rate: waterRate * waterNoise,
          bhp: 2000 - 500 * yearFraction + Math.random() * 100 - 50, // 2000 psi declining to 1500 psi with noise
          thp: 800 - 200 * yearFraction + Math.random() * 50 - 25, // 800 psi declining to 600 psi with noise
          gor: (gasRate * gasNoise) / (oilRate * oilNoise),
          water_cut: (waterRate * waterNoise) / (oilRate * oilNoise + waterRate * waterNoise),
        })
      }
    }

    return {
      metadata: {
        wells: wells,
        startDate: startDate.toISOString().split("T")[0],
        endDate: endDate.toISOString().split("T")[0],
        count: data.length,
      },
      data: data,
    }
  }

  private generateWellData() {
    const wells = []

    for (let i = 1; i <= 10; i++) {
      const wellName = `WELL-${i.toString().padStart(3, "0")}`

      wells.push({
        well_id: i,
        well_name: wellName,
        api_number: `12345${i.toString().padStart(5, "0")}`,
        latitude: 29.5 + Math.random() * 1,
        longitude: -95.2 - Math.random() * 1,
        kb_elevation: 100 + Math.random() * 50,
        total_depth: 10000 + Math.random() * 2000,
        completion_date: new Date(2020, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1)
          .toISOString()
          .split("T")[0],
        formation: ["Wolfcamp", "Eagle Ford", "Bakken", "Marcellus", "Permian"][Math.floor(Math.random() * 5)],
        status: Math.random() > 0.2 ? "Active" : "Inactive",
        completions: [
          {
            zone: "Upper",
            top_md: 9000 + Math.random() * 500,
            bottom_md: 9500 + Math.random() * 500,
            perforations: Math.floor(Math.random() * 20) + 10,
          },
          {
            zone: "Lower",
            top_md: 10000 + Math.random() * 500,
            bottom_md: 10500 + Math.random() * 500,
            perforations: Math.floor(Math.random() * 20) + 10,
          },
        ],
      })
    }

    return {
      metadata: {
        count: wells.length,
        fields: [
          "well_id",
          "well_name",
          "api_number",
          "latitude",
          "longitude",
          "kb_elevation",
          "total_depth",
          "completion_date",
          "formation",
          "status",
          "completions",
        ],
      },
      wells: wells,
    }
  }

  private generateReservoirProperties() {
    const gridSize = { nx: 50, ny: 50, nz: 10 }
    const properties = []

    // Generate a subset of grid blocks for demonstration
    for (let i = 0; i < 100; i++) {
      const x = Math.floor(Math.random() * gridSize.nx)
      const y = Math.floor(Math.random() * gridSize.ny)
      const z = Math.floor(Math.random() * gridSize.nz)

      properties.push({
        block_id: `${x},${y},${z}`,
        porosity: 0.1 + Math.random() * 0.2, // 10-30%
        permeability_x: 10 + Math.random() * 990, // 10-1000 mD
        permeability_y: 10 + Math.random() * 990, // 10-1000 mD
        permeability_z: 1 + Math.random() * 99, // 1-100 mD
        net_to_gross: 0.7 + Math.random() * 0.3, // 70-100%
        water_saturation: 0.2 + Math.random() * 0.3, // 20-50%
        pressure: 3000 + Math.random() * 2000, // 3000-5000 psi
        temperature: 150 + Math.random() * 100, // 150-250 °F
      })
    }

    return {
      metadata: {
        gridSize: gridSize,
        count: properties.length,
      },
      properties: properties,
    }
  }

  private generatePVTData() {
    const pressurePoints = Array.from({ length: 20 }, (_, i) => 500 + i * 250) // 500-5250 psi
    const pvtData = []

    // Oil properties
    const oilPvtData = pressurePoints.map((pressure) => {
      const bubblePoint = 3000
      const isAboveBubblePoint = pressure >= bubblePoint

      return {
        pressure: pressure,
        bo: isAboveBubblePoint
          ? 1.1 + 0.1 * (1 - Math.exp(-(bubblePoint - 500) / 2000))
          : 1.1 + 0.1 * (1 - Math.exp(-(pressure - 500) / 2000)),
        viscosity: isAboveBubblePoint
          ? 0.5 + 0.5 * Math.exp(-(pressure - bubblePoint) / 1000)
          : 0.5 + 0.5 * Math.exp(-(bubblePoint - pressure) / 2000),
        rs: isAboveBubblePoint ? 600 : 600 * (pressure / bubblePoint),
        density: isAboveBubblePoint
          ? 45 + 5 * Math.exp(-(pressure - bubblePoint) / 1000)
          : 45 + 5 * Math.exp(-(bubblePoint - pressure) / 2000),
      }
    })

    // Gas properties
    const gasPvtData = pressurePoints.map((pressure) => {
      return {
        pressure: pressure,
        bg: 0.01 * (5000 / pressure),
        viscosity: 0.01 + 0.005 * (pressure / 5000),
        z_factor: 1 - 0.2 * (pressure / 5000),
      }
    })

    return {
      metadata: {
        fluid_type: "Black Oil",
        temperature: 180, // °F
        api_gravity: 35,
        gas_gravity: 0.65,
      },
      oil_pvt: oilPvtData,
      gas_pvt: gasPvtData,
    }
  }

  private getDatabaseVersion(dbType: DatabaseType): string {
    switch (dbType) {
      case "postgresql":
        return "14.5"
      case "mysql":
        return "8.0.28"
      case "sqlserver":
        return "2019"
      case "oracle":
        return "19c"
      case "mongodb":
        return "5.0.6"
      case "influxdb":
        return "2.6"
      case "ppdm":
        return "3.9"
      case "osdu":
        return "0.12.0"
      default:
        return "Unknown"
    }
  }
}

// Factory function to create appropriate connector based on database type
export function createDatabaseConnector(config: DatabaseConfig): DatabaseConnector {
  return new DatabaseConnector(config)
}

// Predefined database configurations
export const predefinedDatabases: DatabaseConfig[] = [
  {
    id: "production-db",
    name: "Production Database",
    type: "postgresql",
    host: "db.company.com",
    port: 5432,
    database: "production_data",
    username: "prod_user",
    password: "********",
    ssl: true,
    connectionPool: 10,
    schema: "petroleum",
    status: { connected: false },
  },
  {
    id: "well-db",
    name: "Well Database",
    type: "sqlserver",
    host: "welldb.company.com",
    port: 1433,
    database: "well_data",
    username: "well_user",
    password: "********",
    connectionPool: 5,
    status: { connected: false },
  },
  {
    id: "ppdm-db",
    name: "PPDM Database",
    type: "ppdm",
    host: "ppdm.company.com",
    port: 5432,
    database: "ppdm_39",
    username: "ppdm_user",
    password: "********",
    schema: "ppdm39",
    status: { connected: false },
  },
  {
    id: "time-series-db",
    name: "Time Series Database",
    type: "influxdb",
    host: "tsdb.company.com",
    port: 8086,
    database: "sensor_data",
    username: "tsdb_user",
    password: "********",
    status: { connected: false },
  },
]
