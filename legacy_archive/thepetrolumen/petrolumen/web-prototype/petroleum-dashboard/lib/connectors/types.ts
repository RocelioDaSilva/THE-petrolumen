export type SimulationJobStatus = "queued" | "running" | "completed" | "failed" | "canceled"
// Types for simulation engines and database connections

export type SimulationEngineType =
  | "eclipse"
  | "cmg"
  | "tnavigator"
  | "intersect"
  | "mores"
  | "imex"
  | "stars"
  | "gem"
  | "custom"

export type DatabaseType =
  | "postgresql"
  | "mysql"
  | "sqlserver"
  | "oracle"
  | "mongodb"
  | "influxdb"
  | "ppdm"
  | "osdu"
  | "custom"

export interface ConnectionStatus {
  connected: boolean
  lastConnected?: Date
  error?: string
  version?: string
  license?: {
    valid: boolean
    expiresAt?: Date
    features?: string[]
  }
}

export interface SimulationEngineConfig {
  id: string
  name: string
  type: SimulationEngineType
  version: string
  executable: string
  workingDirectory: string
  licenseServer?: string
  licensePort?: number
  maxCores?: number
  maxMemory?: number
  defaultTemplates?: string[]
  customParameters?: Record<string, string>
  status: ConnectionStatus
}

export interface DatabaseConfig {
  id: string
  name: string
  type: DatabaseType
  host: string
  port: number
  database: string
  username: string
  password: string
  ssl?: boolean
  connectionPool?: number
  schema?: string
  customParameters?: Record<string, string>
  status: ConnectionStatus
}

export interface DataSource {
  id: string
  name: string
  type: "simulation" | "database" | "file" | "api"
  config: SimulationEngineConfig | DatabaseConfig
  lastAccessed?: Date
  createdAt: Date
  updatedAt: Date
}

export interface SimulationJob {
  id: string
  name: string
  engineId: string
  status: SimulationJobStatus
  progress: number
  startTime?: Date
  endTime?: Date
  inputFiles: string[]
  outputFiles: string[]
  parameters: Record<string, any>
  results?: Record<string, any>
  error?: string
  createdAt: Date
  updatedAt: Date
}

export interface DataQuery {
  id: string
  sourceId: string
  query: string
  parameters?: Record<string, any>
  results?: any
  status: "pending" | "running" | "completed" | "failed"
  error?: string
  executionTime?: number
  createdAt: Date
  updatedAt: Date
}
