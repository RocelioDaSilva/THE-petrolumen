"use client";

import React, { useState, useEffect, FormEvent } from "react";
import {
  uploadWellData,
  getWellDataPreview,
  getWellStatistics,
  listLoadedWells,
  adminClearAllData,
  WellDataPreview,
  WellStatistics,
  UploadResponse,
  ApiErrorResponse,
} from "@/lib/backendClient"; // Assuming backendClient.ts is in lib

const WellDataDemo: React.FC = () => {
  const [loadedWells, setLoadedWells] = useState<string[]>([]);
  const [selectedWell, setSelectedWell] = useState<string>("");
  const [previewData, setPreviewData] = useState<WellDataPreview[] | null>(null);
  const [statistics, setStatistics] = useState<WellStatistics | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const [wellNameToUpload, setWellNameToUpload] = useState<string>("TestWell");
  const [filesToUpload, setFilesToUpload] = useState<FileList | null>(null);

  const fetchLoadedWells = async () => {
    setIsLoading(true);
    setError("");
    try {
      const wells = await listLoadedWells();
      setLoadedWells(wells);
      if (wells.length > 0 && !selectedWell) {
        setSelectedWell(wells[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch loaded wells.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLoadedWells();
  }, []);

  useEffect(() => {
    if (selectedWell) {
      handleFetchPreview();
      handleFetchStatistics();
    } else {
      setPreviewData(null);
      setStatistics(null);
    }
  }, [selectedWell]);

  const handleFetchPreview = async () => {
    if (!selectedWell) return;
    setIsLoading(true);
    setError("");
    setPreviewData(null);
    try {
      const data = await getWellDataPreview(selectedWell);
      setPreviewData(data);
    } catch (err: any) {
      setError(`Preview error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchStatistics = async () => {
    if (!selectedWell) return;
    setIsLoading(true);
    setError("");
    setStatistics(null);
    try {
      const data = await getWellStatistics(selectedWell);
      setStatistics(data);
    } catch (err: any) {
      setError(`Statistics error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!filesToUpload || filesToUpload.length === 0 || !wellNameToUpload) {
      setError("Please select files and enter a well name for upload.");
      return;
    }
    setIsLoading(true);
    setError("");
    setUploadStatus("");
    try {
      const response: UploadResponse = await uploadWellData(wellNameToUpload, filesToUpload);
      setUploadStatus(response.message || "Upload successful!");
      // Refresh loaded wells list
      fetchLoadedWells();
      // Optionally, select the newly uploaded well
      setSelectedWell(wellNameToUpload);
    } catch (err: any) {
      setError(`Upload error: ${err.message}`);
      setUploadStatus("Upload failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearData = async () => {
    if (!confirm("Are you sure you want to delete all in-memory well data on the backend?")) {
        return;
    }
    setIsLoading(true);
    setError("");
    try {
        const response = await adminClearAllData();
        alert(response.message);
        setLoadedWells([]);
        setSelectedWell("");
        setPreviewData(null);
        setStatistics(null);
        setUploadStatus("");
    } catch (err: any) {
        setError(`Clear data error: ${err.message}`);
    } finally {
        setIsLoading(false);
    }
  };


  return (
    <div style={{ fontFamily: "sans-serif", padding: "20px", maxWidth: "800px", margin: "auto" }}>
      <h2>Well Data API Demo</h2>

      {isLoading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      <section style={{ marginBottom: "20px", padding: "10px", border: "1px solid #eee" }}>
        <h3>Upload Well Data</h3>
        <form onSubmit={handleFileUpload}>
          <div>
            <label htmlFor="wellNameUpload">Well Name: </label>
            <input
              id="wellNameUpload"
              type="text"
              value={wellNameToUpload}
              onChange={(e) => setWellNameToUpload(e.target.value)}
              required
              style={{marginRight: "10px"}}
            />
          </div>
          <div style={{marginTop: "10px", marginBottom: "10px"}}>
            <label htmlFor="fileUpload">Select CSV File(s): </label>
            <input
              id="fileUpload"
              type="file"
              multiple
              accept=".csv"
              onChange={(e) => setFilesToUpload(e.target.files)}
              required
            />
          </div>
          <button type="submit" disabled={isLoading}>
            Upload Data
          </button>
        </form>
        {uploadStatus && <p>{uploadStatus}</p>}
      </section>

      <section style={{ marginBottom: "20px", padding: "10px", border: "1px solid #eee" }}>
        <h3>View Well Data</h3>
        <div>
          <label htmlFor="wellSelect">Select Well: </label>
          <select
            id="wellSelect"
            value={selectedWell}
            onChange={(e) => setSelectedWell(e.target.value)}
            disabled={isLoading || loadedWells.length === 0}
            style={{marginRight: "10px"}}
          >
            <option value="" disabled>
              {loadedWells.length === 0 ? "No wells loaded" : "Select a well"}
            </option>
            {loadedWells.map((well) => (
              <option key={well} value={well}>
                {well}
              </option>
            ))}
          </select>
          <button onClick={fetchLoadedWells} disabled={isLoading} style={{marginRight: "5px"}}>Refresh Well List</button>
        </div>

        {selectedWell && (
          <>
            <h4>Preview for: {selectedWell}</h4>
            {previewData ? (
              <pre style={{ background: "#f4f4f4", padding: "10px", overflowX: "auto" }}>
                {JSON.stringify(previewData, null, 2)}
              </pre>
            ) : (
              <p>No preview data available or loading...</p>
            )}

            <h4>Statistics for: {selectedWell}</h4>
            {statistics ? (
              <pre style={{ background: "#f4f4f4", padding: "10px", overflowX: "auto" }}>
                {JSON.stringify(statistics, null, 2)}
              </pre>
            ) : (
              <p>No statistics available or loading...</p>
            )}
          </>
        )}
      </section>

      <section style={{ marginTop: "30px", padding: "10px", border: "1px solid #fcc" }}>
        <h3>Admin Actions</h3>
        <button onClick={handleClearData} disabled={isLoading} style={{backgroundColor: "#ffdddd"}}>
            Clear All In-Memory Well Data (Admin)
        </button>
      </section>
    </div>
  );
};

export default WellDataDemo;
