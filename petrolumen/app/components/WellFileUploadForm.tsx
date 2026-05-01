"use client";

import React, { useState } from "react";
import { uploadWellData, UploadResponse } from "@/lib/backendClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Upload, Loader2 } from "lucide-react";

interface WellFileUploadFormProps {
  onUploadSuccess: (response: UploadResponse, wellName: string) => void;
}

export const WellFileUploadForm: React.FC<WellFileUploadFormProps> = ({
  onUploadSuccess,
}) => {
  const [wellName, setWellName] = useState<string>("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(e.target.files);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wellName || !files) {
      setError("Please provide a well name and select at least one CSV file.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await uploadWellData(wellName, files);
      onUploadSuccess(response, wellName);
      setWellName("");
      // Reset file input
      const fileInput = document.getElementById("well-files") as HTMLInputElement;
      if (fileInput) fileInput.value = "";
      setFiles(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Well Data
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="well-name">Well Name</Label>
            <Input
              id="well-name"
              placeholder="e.g., Well-001"
              value={wellName}
              onChange={(e) => setWellName(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="well-files">CSV Files</Label>
            <Input
              id="well-files"
              type="file"
              accept=".csv"
              multiple
              onChange={handleFileChange}
              disabled={isLoading}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={isLoading || !wellName || !files}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              "Upload Data"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
