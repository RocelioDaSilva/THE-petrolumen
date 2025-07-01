"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
// import { SidebarTrigger } from "@/components/ui/sidebar" // SidebarTrigger is no longer needed
import { Loader2, CheckCircle, XCircle } from "lucide-react"
import { invoke } from '@tauri-apps/api/tauri'

// Define the status enum to match Rust's ModuleStatusEnum (after serialization)
type ModuleStatusType = "active" | "inactive" | "error";

interface ModuleStatus {
  name: string;
  status: ModuleStatusType; // This will align with the serialized Rust enum
  description: string;
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
        // Not running in Tauri or tauri API not available (e.g. web browser)
        console.log('Not running in Tauri or Tauri API not available.')
        // Set mock data for web development if not in Tauri
        if (!window.__TAURI_IPC__) {
            setModules([
                { name: "Web: Reservoir Simulation", status: "active", description: "Mock data for web" },
                { name: "Web: Production Analysis", status: "inactive", description: "Mock data for web" },
            ]);
            setLoading(false);
        }
      }
    }
    checkTauri()
    
    const fetchStatus = async () => {
      if (!window.__TAURI_IPC__) {
        // Already handled by checkTauri for non-Tauri environments or if API fails
        // You might want to set loading to false here if not already handled
        if (modules.length === 0) setLoading(false); // If checkTauri didn't set modules
        return;
      }
      try {
        console.log("Attempting to invoke get_module_statuses");
        const result = await invoke<ModuleStatus[]>('get_module_statuses');
        console.log("Received from Tauri:", result);
        setModules(result);
      } catch (error) {
        console.error("Failed to fetch status from Tauri:", error)
        // Fallback or error display
        setModules([
            { name: "Error Fetching Data", status: "error", description: "Could not connect to backend" }
        ]);
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, []) // modules was removed from dependency array, as it caused an infinite loop

  const getStatusIcon = (status: ModuleStatusType) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />
      case "inactive": // Explicitly handle inactive
        return <div className="h-4 w-4 rounded-full bg-gray-300" />
      default: // Fallback, though should not be reached with strict types
        return <div className="h-4 w-4 rounded-full bg-yellow-300" />
    }
  }

  const getStatusBadge = (status: ModuleStatusType) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Active
          </Badge>
        )
      case "error":
        return <Badge variant="destructive">Error</Badge>
      case "inactive": // Explicitly handle inactive
        return <Badge variant="secondary">Inactive</Badge>
      default: // Fallback
        return <Badge variant="outline">Unknown</Badge>
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
