import { createSimulationEngineConnector, predefinedEngines } from "./simulation-engines"
import { createDatabaseConnector, predefinedDatabases } from "./databases"
import type { DataSource, SimulationEngineConfig, DatabaseConfig, SimulationJob, DataQuery } from "./types"

// Singleton class to manage all connections
class ConnectionManager {
  private static instance: ConnectionManager

  private simulationEngines: Map<string, ReturnType<typeof createSimulationEngineConnector>> = new Map()
  private databases: Map<string, ReturnType<typeof createDatabaseConnector>> = new Map()
  private dataSources: Map<string, DataSource> = new Map()

  private constructor() {
    // Initialize with predefined engines and databases
    this.initializePredefinedConnections()
  }

  public static getInstance(): ConnectionManager {
    if (!ConnectionManager.instance) {
      ConnectionManager.instance = new ConnectionManager()
    }
    return ConnectionManager.instance
  }

  private initializePredefinedConnections() {
    // Add predefined simulation engines
    for (const engineConfig of predefinedEngines) {
      this.addSimulationEngine(engineConfig)
    }

    // Add predefined databases
    for (const dbConfig of predefinedDatabases) {
      this.addDatabase(dbConfig)
    }
  }

  // Simulation Engine methods
  public addSimulationEngine(config: SimulationEngineConfig): DataSource {
    const connector = createSimulationEngineConnector(config)
    this.simulationEngines.set(config.id, connector)

    const dataSource: DataSource = {
      id: config.id,
      name: config.name,
      type: "simulation",
      config: config,
      createdAt: new Date(),
      updatedAt: new Date(),
    }

    this.dataSources.set(config.id, dataSource)
    return dataSource
  }

  public async connectSimulationEngine(id: string): Promise<boolean> {
    const connector = this.simulationEngines.get(id)
    if (!connector) {
      throw new Error(`Simulation engine ${id} not found`)
    }

    const success = await connector.connect()

    // Update data source
    const dataSource = this.dataSources.get(id)
    if (dataSource) {
      dataSource.config = connector.getConfig()
      dataSource.updatedAt = new Date()
    }

    return success
  }

  public async disconnectSimulationEngine(id: string): Promise<boolean> {
    const connector = this.simulationEngines.get(id)
    if (!connector) {
      throw new Error(`Simulation engine ${id} not found`)
    }

    const success = await connector.disconnect()

    // Update data source
    const dataSource = this.dataSources.get(id)
    if (dataSource) {
      dataSource.config = connector.getConfig()
      dataSource.updatedAt = new Date()
    }

    return success
  }

  public async submitSimulationJob(
    engineId: string,
    job: Omit<SimulationJob, "id" | "status" | "progress" | "createdAt" | "updatedAt">,
  ): Promise<SimulationJob> {
    const connector = this.simulationEngines.get(engineId)
    if (!connector) {
      throw new Error(`Simulation engine ${engineId} not found`)
    }

    return await connector.submitJob(job)
  }

  public async getSimulationJobStatus(engineId: string, jobId: string): Promise<SimulationJob> {
    const connector = this.simulationEngines.get(engineId)
    if (!connector) {
      throw new Error(`Simulation engine ${engineId} not found`)
    }

    return await connector.getJobStatus(jobId)
  }

  public async cancelSimulationJob(engineId: string, jobId: string): Promise<SimulationJob> {
    const connector = this.simulationEngines.get(engineId)
    if (!connector) {
      throw new Error(`Simulation engine ${engineId} not found`)
    }

    return await connector.cancelJob(jobId)
  }

  public getSimulationEngineConfig(id: string): SimulationEngineConfig | undefined {
    const connector = this.simulationEngines.get(id)
    return connector?.getConfig()
  }

  public getAllSimulationEngines(): SimulationEngineConfig[] {
    return Array.from(this.simulationEngines.values()).map((connector) => connector.getConfig())
  }

  // Database methods
  public addDatabase(config: DatabaseConfig): DataSource {
    const connector = createDatabaseConnector(config)
    this.databases.set(config.id, connector)

    const dataSource: DataSource = {
      id: config.id,
      name: config.name,
      type: "database",
      config: config,
      createdAt: new Date(),
      updatedAt: new Date(),
    }

    this.dataSources.set(config.id, dataSource)
    return dataSource
  }

  public async connectDatabase(id: string): Promise<boolean> {
    const connector = this.databases.get(id)
    if (!connector) {
      throw new Error(`Database ${id} not found`)
    }

    const success = await connector.connect()

    // Update data source
    const dataSource = this.dataSources.get(id)
    if (dataSource) {
      dataSource.config = connector.getConfig()
      dataSource.updatedAt = new Date()
    }

    return success
  }

  public async disconnectDatabase(id: string): Promise<boolean> {
    const connector = this.databases.get(id)
    if (!connector) {
      throw new Error(`Database ${id} not found`)
    }

    const success = await connector.disconnect()

    // Update data source
    const dataSource = this.dataSources.get(id)
    if (dataSource) {
      dataSource.config = connector.getConfig()
      dataSource.updatedAt = new Date()
    }

    return success
  }

  public async executeQuery(
    databaseId: string,
    query: Omit<DataQuery, "id" | "status" | "createdAt" | "updatedAt">,
  ): Promise<DataQuery> {
    const connector = this.databases.get(databaseId)
    if (!connector) {
      throw new Error(`Database ${databaseId} not found`)
    }

    return await connector.executeQuery(query)
  }

  public async getQueryStatus(databaseId: string, queryId: string): Promise<DataQuery> {
    const connector = this.databases.get(databaseId)
    if (!connector) {
      throw new Error(`Database ${databaseId} not found`)
    }

    return await connector.getQueryStatus(queryId)
  }

  public async cancelQuery(databaseId: string, queryId: string): Promise<DataQuery> {
    const connector = this.databases.get(databaseId)
    if (!connector) {
      throw new Error(`Database ${databaseId} not found`)
    }

    return await connector.cancelQuery(queryId)
  }

  public getDatabaseConfig(id: string): DatabaseConfig | undefined {
    const connector = this.databases.get(id)
    return connector?.getConfig()
  }

  public getAllDatabases(): DatabaseConfig[] {
    return Array.from(this.databases.values()).map((connector) => connector.getConfig())
  }

  // Data Source methods
  public getDataSource(id: string): DataSource | undefined {
    return this.dataSources.get(id)
  }

  public getAllDataSources(): DataSource[] {
    return Array.from(this.dataSources.values())
  }

  public getDataSourcesByType(type: DataSource["type"]): DataSource[] {
    return Array.from(this.dataSources.values()).filter((ds) => ds.type === type)
  }

  public removeDataSource(id: string): boolean {
    const dataSource = this.dataSources.get(id)
    if (!dataSource) {
      return false
    }

    // Disconnect if connected
    if (dataSource.type === "simulation") {
      const connector = this.simulationEngines.get(id)
      if (connector && connector.getConfig().status.connected) {
        connector.disconnect()
      }
      this.simulationEngines.delete(id)
    } else if (dataSource.type === "database") {
      const connector = this.databases.get(id)
      if (connector && connector.getConfig().status.connected) {
        connector.disconnect()
      }
      this.databases.delete(id)
    }

    return this.dataSources.delete(id)
  }
}

export const connectionManager = ConnectionManager.getInstance()
