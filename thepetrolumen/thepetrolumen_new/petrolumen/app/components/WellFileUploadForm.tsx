"use client";

import React, { useState, FormEvent } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadResponse, uploadWellData } from '@/lib/backendClient'; // Import uploadWellData here

interface WellFileUploadFormProps {
  onUploadSuccess: (response: UploadResponse, uploadedWellName: string) => void;
  setIsLoadingGlobal: (isLoading: boolean) => void;
  setErrorGlobal: (error: string) => void;
  isLoadingGlobal: boolean;
}

export const WellFileUploadForm: React.FC<WellFileUploadFormProps> = ({
  onUploadSuccess,
  setIsLoadingGlobal,
  setErrorGlobal,
  isLoadingGlobal
}) => {
  const [wellNameToUpload, setWellNameToUpload] = useState<string>("TestWell");
  const [filesToUpload, setFilesToUpload] = useState<FileList | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  // uploadWellData is now imported at the top of the file.

  const handleFileUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!filesToUpload || filesToUpload.length === 0 || !wellNameToUpload) {
      setErrorGlobal("Please select files and enter a well name for upload.");
      return;
    }
    setIsLoadingGlobal(true);
    setErrorGlobal("");
    setUploadStatus("");
    try {
      // This needs to be adapted if uploadWellData is not directly importable here easily
      // Or if backendClient needs specific setup (e.g. token) that should be managed by a parent
      const response: UploadResponse = await uploadWellData(wellNameToUpload, filesToUpload);
      setUploadStatus(response.message || "Upload successful!");
      onUploadSuccess(response, wellNameToUpload);
    } catch (err) {
      if (err instanceof Error) {
        setErrorGlobal(`Upload error: ${err.message}`);
      } else {
        setErrorGlobal("Upload error: An unexpected error occurred.");
      }
      setUploadStatus("Upload failed.");
      console.error("Error in handleFileUpload:", err);
    } finally {
      setIsLoadingGlobal(false);
    }
  };

  return (
    <Card className="mb-5">
      <CardHeader>
        <CardTitle>Upload Well Data</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleFileUpload} className="space-y-4">
          <div>
            <Label htmlFor="wellNameUpload" className="mb-1 block">Well Name: </Label>
            <Input
              id="wellNameUpload"
              type="text"
              value={wellNameToUpload}
              onChange={(e) => setWellNameToUpload(e.target.value)}
              required
              className="max-w-xs"
              disabled={isLoadingGlobal}
            />
          </div>
          <div className="my-3">
            <Label htmlFor="fileUpload" className="mb-1 block">Select CSV File(s): </Label>
            <Input
              id="fileUpload"
              type="file"
              multiple
              accept=".csv"
              onChange={(e) => setFilesToUpload(e.target.files)}
              required
              className="max-w-xs file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
              disabled={isLoadingGlobal}
            />
          </div>
          <Button type="submit" disabled={isLoadingGlobal}>
            Upload Data
          </Button>
        </form>
        {uploadStatus && <p className="mt-3 text-sm" aria-live="polite">{uploadStatus}</p>}
      </CardContent>
    </Card>
  );
};
