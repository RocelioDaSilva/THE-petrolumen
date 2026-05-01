"use client";

import React, { useState, useEffect } from "react";
import {
  getWellDataPreview,
  getWellStatistics,
  listLoadedWells,
  WellDataPreview,
  WellStatistics,
  UploadResponse,
} from "@/lib/backendClient";
import { useAppStore } from "@/stores/appStore";

// Import child components
import { AuthStatusDisplay } from "./AuthStatusDisplay";
import { WellFileUploadForm } from "./WellFileUploadForm";
import { WellDataSelector } from "./WellDataSelector";
import { WellDataViewer } from "./WellDataViewer";
import { AdminActionsPanel } from "./AdminActionsPanel";
import { LoginForm } from "./LoginForm";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Loader2 } from "lucide-react";

const WellDataDemo: React.FC = () => {
  const { isAuthenticated, selectedWell, setSelectedWell } = useAppStore();

  const [loadedWells, setLoadedWells] = useState<string[]>([]);
  const [previewData, setPreviewData] = useState<WellDataPreview[] | null>(null);
  const [statistics, setStatistics] = useState<WellStatistics | null>(null);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchLoadedWells = async () => {
    setIsLoading(true);
    setError("");
    try {
      const wells = await listLoadedWells();
      setLoadedWells(wells);
      if (wells.length > 0 && !selectedWell) {
        setSelectedWell(wells[0]);
      } else if (wells.length === 0) {
        setSelectedWell(null);
        setPreviewData(null);
        setStatistics(null);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch loaded wells";
      setError(msg);
      setLoadedWells([]);
      setSelectedWell(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchLoadedWells();
    } else {
      setLoadedWells([]);
      setSelectedWell(null);
      setPreviewData(null);
      setStatistics(null);
      setError("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const fetchWellDetails = async (wellName: string) => {
    setIsLoading(true);
    try {
      const [preview, stats] = await Promise.all([
        getWellDataPreview(wellName),
        getWellStatistics(wellName)
      ]);
      setPreviewData(preview);
      setStatistics(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch well details");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedWell && isAuthenticated) {
      fetchWellDetails(selectedWell);
    } else {
      setPreviewData(null);
      setStatistics(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWell, isAuthenticated]);


  const handleUploadSuccess = (response: UploadResponse, uploadedWellName: string) => {
    fetchLoadedWells().then(() => {
        setSelectedWell(uploadedWellName);
    });
  };

  if (!isAuthenticated) {
    return (
      <div className="container max-w-4xl py-10 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">PetroLúmen</h1>
          <p className="text-muted-foreground">Reservoir Engineering Data Management</p>
        </div>
        <LoginForm />
      </div>
    );
  }

  return (
    <div className="container max-w-5xl py-10 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Well Data Management</h1>
          <p className="text-muted-foreground">Upload and analyze reservoir production data</p>
        </div>
        <AuthStatusDisplay />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-8">
          <WellFileUploadForm onUploadSuccess={handleUploadSuccess} />
          <AdminActionsPanel onClearAllData={() => alert("Disabled")} isLoading={isLoading} />
        </div>

        <div className="md:col-span-2 space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Well Explorer</CardTitle>
              <CardDescription>Select a well to view its production statistics and data preview</CardDescription>
            </CardHeader>
            <CardContent>
              <WellDataSelector
                loadedWells={loadedWells}
                onRefreshWells={fetchLoadedWells}
                isLoading={isLoading}
              />

              {isLoading && !previewData ? (
                <div className="flex justify-center py-10">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : (
                <WellDataViewer
                  selectedWell={selectedWell || ""}
                  previewData={previewData}
                  statistics={statistics}
                  isLoading={isLoading}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default WellDataDemo;
