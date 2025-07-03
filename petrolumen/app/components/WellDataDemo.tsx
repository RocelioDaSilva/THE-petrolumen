"use client";

import React, { useState, useEffect } from "react";
import {
  getWellDataPreview,
  getWellStatistics,
  listLoadedWells,
  adminClearAllData, // This function might be removed if endpoint is gone
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
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const WellDataDemo: React.FC = () => {
  const { isAuthenticated } = useAppStore(); // Get auth state

  const [loadedWells, setLoadedWells] = useState<string[]>([]);
  const [selectedWell, setSelectedWell] = useState<string>("");
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
        setSelectedWell("");
        setPreviewData(null);
        setStatistics(null);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(`Failed to fetch loaded wells: ${err.message}. Is the backend running or are you logged in?`);
      } else {
        setError("Failed to fetch loaded wells due to an unexpected error.");
      }
      console.error("Error in fetchLoadedWells:", err);
      // If fetching wells fails (e.g. 401), clear existing well data
      setLoadedWells([]);
      setSelectedWell("");
      setPreviewData(null);
      setStatistics(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) { // Only fetch wells if authenticated
      fetchLoadedWells();
    } else { // Clear data if not authenticated
      setLoadedWells([]);
      setSelectedWell("");
      setPreviewData(null);
      setStatistics(null);
      setError(""); // Clear errors too
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]); // Re-fetch or clear when auth state changes

  const handleFetchPreview = async () => {
    if (!selectedWell || !isAuthenticated) return;
    setIsLoading(true);
    setError("");
    setPreviewData(null);
    try {
      const data = await getWellDataPreview(selectedWell);
      setPreviewData(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(`Preview error for ${selectedWell}: ${err.message}`);
      } else {
        setError(`Preview error for ${selectedWell}: An unexpected error occurred.`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchStatistics = async () => {
    if (!selectedWell || !isAuthenticated) return;
    setIsLoading(true);
    setError("");
    setStatistics(null);
    try {
      const data = await getWellStatistics(selectedWell);
      setStatistics(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(`Statistics error for ${selectedWell}: ${err.message}`);
      } else {
        setError(`Statistics error for ${selectedWell}: An unexpected error occurred.`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedWell && isAuthenticated) {
      handleFetchPreview();
      handleFetchStatistics();
    } else {
      setPreviewData(null);
      setStatistics(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWell, isAuthenticated]);


  const handleUploadSuccess = (response: UploadResponse, uploadedWellName: string) => {
    if (isAuthenticated) { // Re-fetch wells only if authenticated
        fetchLoadedWells().then(() => {
            setSelectedWell(uploadedWellName);
        });
    }
  };

  const handleClearAllData = async () => {
    // Note: The backend endpoint for adminClearAllData was removed.
    // This function would need to be updated if a replacement admin delete function is added.
    // For now, it will likely error out or do nothing if called.
    // Consider disabling this button or removing the feature if endpoint is gone.
    alert("Admin clear all data functionality is currently disabled as the backend endpoint was removed.");
    // if (!confirm("Are you sure you want to delete all backend well data? This action cannot be undone.")) {
    //     return;
    // }
    // setIsLoading(true);
    // setError("");
    // try {
    //     const response = await adminClearAllData(); // This will fail
    //     alert(response.message);
    //     fetchLoadedWells();
    // } catch (err) {
    //   // ... error handling ...
    // } finally {
    //     setIsLoading(false);
    // }
  };

  return (
    <div className="font-sans p-5 max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-center">Well Data Management Demo</h2>

      <AuthStatusDisplay /> {/* This component handles its own dummy login/logout for now */}

      {error && <p className="text-red-600 bg-red-100 p-3 rounded-md my-4 text-center" aria-live="assertive">Error: {error}</p>}

      {!isAuthenticated && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Please Login</CardTitle>
            <CardContent>
              <p className="mb-4 text-muted-foreground">You need to log in to manage and view well data.</p>
              <LoginForm />
            </CardContent>
          </CardHeader>
        </Card>
      )}

      {isAuthenticated && (
        <>
          {/* Error message moved above the conditional block to be visible even when not authenticated if a global error occurs */}
          {/* isLoading for well list is now implicitly handled by isAuthenticated block or specific component states */}
          {isLoading && !selectedWell && <p className="text-center my-4 text-blue-600">Loading well list...</p>}

          <WellFileUploadForm
            onUploadSuccess={handleUploadSuccess}
            setIsLoadingGlobal={setIsLoading}
            setErrorGlobal={setError}
            isLoadingGlobal={isLoading}
          />

          <Card>
            <CardHeader>
              <CardTitle>View Well Data</CardTitle>
            </CardHeader>
            <CardContent>
              <WellDataSelector
                loadedWells={loadedWells}
                selectedWell={selectedWell}
                onSelectedWellChange={setSelectedWell}
                onRefreshWells={fetchLoadedWells}
                isLoading={isLoading}
              />
              <WellDataViewer
                selectedWell={selectedWell}
                previewData={previewData}
                statistics={statistics}
                // Show loading specifically for viewer if a well is selected and parent is loading its data
                isLoading={isLoading && !!selectedWell && (!previewData || !statistics)}
              />
            </CardContent>
          </Card>

          {/* AdminActionsPanel might also check for admin role internally from store */}
          <AdminActionsPanel
            onClearAllData={handleClearAllData}
            isLoading={isLoading}
          />
        </>
      )}
    </div>
  );
};

export default WellDataDemo;
