"use client"

import { useState, useEffect } from "react"
import { Database, Server, Plus, RefreshCw, Trash2, Check, X, AlertCircle, Play, Pause, Download } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { cn } from "@/lib/utils"

import { connectionManager } from "../../lib/connectors/connection-manager"
import type { SimulationEngineConfig, DatabaseConfig, SimulationJob, DataQuery } from "../../lib/connectors/types"

export function ConnectionManagerUI() {
  const [activeTab, setActiveTab] = useState("simulation-engines")
  const [simulationEngines, setSimulationEngines] = useState<SimulationEngineConfig[]>([])
  const [databases, setDatabases] = useState<DatabaseConfig[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedEngine, setSelectedEngine] = useState<SimulationEngineConfig | null>(null)
  const [selectedDatabase, setSelectedDatabase] = useState<DatabaseConfig | null>(null)
  const [showAddEngineDialog, setShowAddEngineDialog] = useState(false)
  const [showAddDatabaseDialog, setShowAddDatabaseDialog] = useState(false)
  const [activeJobs, setActiveJobs] = useState<SimulationJob[]>([])
  const [activeQueries, setActiveQueries] = useState<DataQuery[]>([])

  // Load data sources on component mount
  useEffect(() => {
    loadDataSources()
  }, [])

  const loadDataSources = () => {
    setIsLoading(true)
    
    // Get all simulation engines
    const engines = connectionManager.getAllSimulationEngines()
    setSimulationEngines(engines)
    
    // Get all databases
    const dbs = connectionManager.getAllDatabases()
    setDatabases(dbs)
    
    setIsLoading(false)
  }

  const handleConnectEngine = async (engineId: string) => {
    try {
      await connectionManager.connectSimulationEngine(engineId)
      loadDataSources() // Refresh data
    } catch (error) {
      console.error("Failed to connect to simulation engine:", error)
      // In a real app, show an error toast/notification
    }
  }

  const handleDisconnectEngine = async (engineId: string) => {
    try {
      await connectionManager.disconnectSimulationEngine(engineId)
      loadDataSources() // Refresh data
    } catch (error) {
      console.error("Failed to disconnect from simulation engine:", error)
      // In a real app, show an error toast/notification
    }
  }

  const handleConnectDatabase = async (databaseId: string) => {
    try {
      await connectionManager.connectDatabase(databaseId)
      loadDataSources() // Refresh data
    } catch (error) {
      console.error("Failed to connect to database:", error)
      // In a real app, show an error toast/notification
    }
  }

  const handleDisconnectDatabase = async (databaseId: string) => {
    try {
      await connectionManager.disconnectDatabase(databaseId)
      loadDataSources() // Refresh data
    } catch (error) {
      console.error("Failed to disconnect from database:", error)
      // In a real app, show an error toast/notification
    }
  }

  const handleRemoveEngine = (engineId: string) => {
    connectionManager.removeDataSource(engineId)
    loadDataSources() // Refresh data
  }

  const handleRemoveDatabase = (databaseId: string) => {
    connectionManager.removeDataSource(databaseId)
    loadDataSources() // Refresh data
  }

  const handleAddEngine = (engineConfig: SimulationEngineConfig) => {
    connectionManager.addSimulationEngine(engineConfig)
    setShowAddEngineDialog(false)
    loadDataSources() // Refresh data
  }

  const handleAddDatabase = (dbConfig: DatabaseConfig) => {
    connectionManager.addDatabase(dbConfig)
    setShowAddDatabaseDialog(false)
    loadDataSources() // Refresh data
  }

  const handleRunTestSimulation = async (engineId: string) => {
    try {
      const job = await connectionManager.submitSimulationJob(engineId, {
        name: "Test Simulation",
        engineId: engineId,
        inputFiles: ["test_input.DATA"],
        outputFiles: ["test_output.RSM"],
        parameters: {
          simulationType: "black-oil",
          timeSteps: 10,
          reportFrequency: 1
        }
      })
      
      // Add job to active jobs
      setActiveJobs(prev => [...prev, job])
      
      // Poll for job status updates
      const intervalId = setInterval(async () => {
        try {
          const updatedJob = await connectionManager.getSimulationJobStatus(engineId, job.id)
          
          setActiveJobs(prev => 
            prev.map(j => j.id === updatedJob.id ? updatedJob : j)
          )
          
          if (updatedJob.status === "completed" || updatedJob.status === "failed" || updatedJob.status === "canceled") {
            clearInterval(intervalId)
          }
        } catch (error) {
          console.error("Failed to get job status:", error)
          clearInterval(intervalId)
        }
      }, 1000)
      
    } catch (error) {
      console.error("Failed to submit test simulation:", error)
      // In a real app, show an error toast/notification
    }
  }

  const handleRunTestQuery = async (databaseId: string) => {
    try {
      const query = await connectionManager.executeQuery(databaseId, {
        sourceId: databaseId,
        query: "SELECT * FROM production_data WHERE date > '2022-01-01' LIMIT 100",
        parameters: {
          startDate: "2022-01-01",
          limit: 100
        }
      })
      
      // Add query to active queries
      setActiveQueries(prev => [...prev, query])
      
      // Poll for query status updates
      const intervalId = setInterval(async () => {
        try {
          const updatedQuery = await connectionManager.getQueryStatus(databaseId, query.id)
          
          setActiveQueries(prev => 
            prev.map(q => q.id === updatedQuery.id ? updatedQuery : q)
          )
          
          if (updatedQuery.status === "completed" || updatedQuery.status === "failed") {
            clearInterval(intervalId)
          }
        } catch (error) {
          console.error("Failed to get query status:", error)
          clearInterval(intervalId)
        }
      }, 500)
      
    } catch (error) {
      console.error("Failed to execute test query:", error)
      // In a real app, show an error toast/notification
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Gerenciador de Conexões</h2>
          <p className="text-slate-600 dark:text-slate-400">
            Gerencie conexões com simuladores e bancos de dados
          </p>
        </div>
        <Button onClick={loadDataSources} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Atualizar
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="simulation-engines">
            <Server className="h-4 w-4 mr-2" />
            Simuladores
          </TabsTrigger>
          <TabsTrigger value="databases">
            <Database className="h-4 w-4 mr-2" />
            Bancos de Dados
          </TabsTrigger>
        </TabsList>

        {/* Simulation Engines Tab */}
        <TabsContent value="simulation-engines" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddEngineDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Adicionar Simulador
            </Button>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-slate-400" />
                <p className="mt-2 text-slate-600 dark:text-slate-400">Carregando simuladores...</p>
              </div>
            </div>
          ) : simulationEngines.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nenhum simulador configurado</AlertTitle>
              <AlertDescription>
                Adicione um simulador para começar a executar simulações.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {simulationEngines.map((engine) => (
                <Card key={engine.id} className={cn(
                  "transition-all duration-200",
                  engine.status.connected ? "border-green-200 dark:border-green-800" : ""
                )}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center">
                        <Server className="h-5 w-5 mr-2 text-blue-600" />
                        {engine.name}
                      </CardTitle>
                      <Badge variant={engine.status.connected ? "default" : "outline"}>
                        {engine.status.connected ? "Conectado" : "Desconectado"}
                      </Badge>
                    </div>
                    <CardDescription>
                      {engine.type} {engine.version}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pb-2">
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Executável:</span>
                        <span className="font-mono text-xs truncate max-w-[200px]">{engine.executable}</span>
                      </div>
                      {engine.status.connected && engine.status.license && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-400">Licença:</span>
                          <span className={engine.status.license.valid ? "text-green-600" : "text-red-600"}>
                            {engine.status.license.valid ? "Válida" : "Inválida"}
                            {engine.status.license.expiresAt && ` (Expira: ${new Date(engine.status.license.expiresAt).toLocaleDateString()})`}
                          </span>
                        </div>
                      )}
                      {engine.status.connected && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-400">Recursos:</span>
                          <span className="text-slate-900 dark:text-slate-100">
                            {engine.maxCores || "N/A"} cores / {engine.maxMemory || "N/A"} GB
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between pt-2">
                    <div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedEngine(engine)
                          handleRunTestSimulation(engine.id)
                        }}
                        disabled={!engine.status.connected}
                      >
                        <Play className="h-4 w-4 mr-1" />
                        Testar
                      </Button>
                    </div>
                    <div className="flex space-x-2">
                      {engine.status.connected ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDisconnectEngine(engine.id)}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Desconectar
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleConnectEngine(engine.id)}
                        >
                          <Check className="h-4 w-4 mr-1" />
                          Conectar
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-100"
                        onClick={() => handleRemoveEngine(engine.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}

          {/* Active Simulation Jobs */}
          {activeJobs.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-medium mb-4">Simulações Ativas</h3>
              <div className="space-y-4">
                {activeJobs.map((job) => (
                  <Card key={job.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{job.name}</CardTitle>
                        <Badge variant={
                          job.status === "completed" ? "default" :
                          job.status === "failed" ? "destructive" :
                          job.status === "running" ? "default" :
                          "outline"
                        }>
                          {job.status === "completed" ? "Concluído" :
                           job.status === "failed" ? "Falhou" :
                           job.status === "running" ? "Em Execução" :
                           job.status === "queued" ? "Na Fila" :
                           "Cancelado"}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="pb-2">
                      {job.status === "running" && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Progresso</span>
                            <span>{job.progress}%</span>
                          </div>
                          <Progress value={job.progress} className="h-2" />
                        </div>
                      )}
                      {job.status === "completed" && job.results && (
                        <Accordion type="single" collapsible>
                          <AccordionItem value="results">
                            <AccordionTrigger>Ver Resultados</AccordionTrigger>
                            <AccordionContent>
                              <pre className="bg-slate-100 dark:bg-slate-800 p-2 rounded-md text-xs overflow-auto max-h-40">
                                {JSON.stringify(job.results, null, 2)}
                              </pre>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      )}
                      {job.status === "failed" && job.error && (
                        <Alert variant="destructive" className="mt-2">
                          <AlertCircle className="h-4 w-4" />
                          <AlertTitle>Erro</AlertTitle>
                          <AlertDescription>{job.error}</AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                    <CardFooter className="pt-2">
                      <div className="flex justify-end w-full space-x-2">
                        {job.status === "running" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => connectionManager.cancelSimulationJob(job.engineId, job.id)}
                          >
                            <Pause className="h-4 w-4 mr-1" />
                            Cancelar
                          </Button>
                        )}
                        {job.status === "completed" && (
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-1" />
                            Exportar Resultados
                          </Button>
                        )}
                      </div>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Databases Tab */}
        <TabsContent value="databases" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddDatabaseDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Adicionar Banco de Dados
            </Button>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-slate-400" />
                <p className="mt-2 text-slate-600 dark:text-slate-400">Carregando bancos de dados...</p>
              </div>
            </div>
          ) : databases.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nenhum banco de dados configurado</AlertTitle>
              <AlertDescription>
                Adicione um banco de dados para começar a consultar dados.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {databases.map((db) => (
                <Card key={db.id} className={cn(
                  "transition-all duration-200",
                  db.status.connected ? "border-green-200 dark:border-green-800" : ""
                )}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center">
                        <Database className="h-5 w-5 mr-2 text-green-600" />
                        {db.name}
                      </CardTitle>
                      <Badge variant={db.status.connected ? "default" : "outline"}>
                        {db.status.connected ? "Conectado" : "Desconectado"}
                      </Badge>
                    </div>
                    <CardDescription>
                      {db.type} {db.status.version || ""}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pb-2">
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Host:</span>
                        <span className="font-mono text-xs">{db.host}:{db.port}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Database:</span>
                        <span className="font-mono text-xs">{db.database}</span>
                      </div>
                      {db.schema && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-400">Schema:</span>
                          <span className="font-mono text-xs">{db.schema}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between pt-2">
                    <div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedDatabase(db)
                          handleRunTestQuery(db.id)
                        }}
                        // Corrigido: removido caractere inválido e fechamento correto
                      >
                        <Play className="h-4 w-4 mr-1" />
                        Testar
                      </Button>
                    </div>
                    <div className="flex space-x-2">
                      {db.status.connected ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDisconnectDatabase(db.id)}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Desconectar
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleConnectDatabase(db.id)}
                        >
                          <Check className="h-4 w-4 mr-1" />
                          Conectar
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-100"
                        onClick={() => handleRemoveDatabase(db.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
