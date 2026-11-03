"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Loader2, CheckCircle, XCircle } from "lucide-react"
import { invoke } from '@tauri-apps/api/tauri'

interface ModuleStatus {
  name: string
  status: "active" | "inactive" | "error"
  description: string
}

export default function Dashboard() {
  const [modules, setModules] = useState<ModuleStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [tauriVersion, setTauriVersion] = useState<string>("")

  useEffect(() => {
    // Check if we're running in Tauri
    const checkTauri = async () => {
      try {
        const version = await invoke('get_version')
        setTauriVersion(version as string)
      } catch (e) {
        console.log('Not running in Tauri')
      }
    }
    checkTauri()
    
    const fetchStatus = async () => {
      try {
        // Simulated API call - replace with actual endpoint
        await new Promise((resolve) => setTimeout(resolve, 1000))
        setModules([
          { name: "Reservoir Simulation", status: "active", description: "Eclipse, CMG, tNavigator simulators ready" },
          { name: "Production Analysis", status: "active", description: "Decline curve analysis available" },
          { name: "Optimization", status: "active", description: "History matching algorithms ready" },
          { name: "Static Modeling", status: "active", description: "Grid and property models loaded" },
          { name: "Uncertainty Analysis", status: "active", description: "Monte Carlo simulation ready" },
          { name: "Well Testing", status: "active", description: "Pressure analysis tools available" },
          { name: "Economic Analysis", status: "active", description: "Reserves calculation ready" },
          { name: "Visualization", status: "active", description: "3D rendering engine active" },
          { name: "AI Analytics", status: "active", description: "Machine learning models loaded" },
          { name: "Integration", status: "active", description: "Data connectors available" },
        ])
      } catch (error) {
        console.error("Failed to fetch status:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <div className="h-4 w-4 rounded-full bg-gray-300" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Active
          </Badge>
        )
      case "error":
        return <Badge variant="destructive">Error</Badge>
      default:
        return <Badge variant="secondary">Inactive</Badge>
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="px-6 py-8 mx-auto max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 dark:text-white">
              PetroLúmen {tauriVersion && `(${tauriVersion})`}
            </h1>
            <p className="mt-2 text-lg text-gray-600 dark:text-gray-300">
              Plataforma Avançada de Engenharia de Petróleo
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="px-4 py-1">
              Desktop
            </Badge>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid gap-6 mb-8 md:grid-cols-2 lg:grid-cols-3">
          <Card className="bg-white/50 backdrop-blur-lg border-0 shadow-lg dark:bg-gray-800/50">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-blue-100 rounded-lg dark:bg-blue-900">
                  <CheckCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <CardTitle>Sistema</CardTitle>
                  <CardDescription>Status dos Módulos</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                100%
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Todos os módulos operacionais
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/50 backdrop-blur-lg border-0 shadow-lg dark:bg-gray-800/50">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-green-100 rounded-lg dark:bg-green-900">
                  <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle>Simulações</CardTitle>
                  <CardDescription>Status das Simulações</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                24
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Simulações concluídas hoje
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/50 backdrop-blur-lg border-0 shadow-lg dark:bg-gray-800/50">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-purple-100 rounded-lg dark:bg-purple-900">
                  <CheckCircle className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle>IA & Analytics</CardTitle>
                  <CardDescription>Status dos Modelos</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                8
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Modelos de IA ativos
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Modules Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            <div className="col-span-full flex justify-center p-8">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : (
            modules.map((module) => (
              <Card key={module.name} className="bg-white/50 backdrop-blur-lg border-0 shadow-lg hover:shadow-xl transition-shadow dark:bg-gray-800/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{module.name}</CardTitle>
                    {getStatusBadge(module.status)}
                  </div>
                  <CardDescription>{module.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                    {getStatusIcon(module.status)}
                    <span>Última atualização: 2 min atrás</span>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
