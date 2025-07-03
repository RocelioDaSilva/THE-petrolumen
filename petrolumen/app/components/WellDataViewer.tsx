"use client";

import React from 'react';
import { WellDataPreview, WellStatistics } from '@/lib/backendClient'; // Assuming these types are defined

interface WellDataViewerProps {
  selectedWell: string | null;
  previewData: WellDataPreview[] | null;
  statistics: WellStatistics | null;
  isLoading: boolean; // To show loading state if data for selected well is being fetched
}

export const WellDataViewer: React.FC<WellDataViewerProps> = ({
  selectedWell,
  previewData,
  statistics,
  isLoading,
}) => {
  if (!selectedWell) {
    return <p className="text-sm text-muted-foreground">Please select a well to view its data.</p>;
  }

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading data for {selectedWell}...</p>;
  }

  return (
    <div className="space-y-4">
      <div>
        <h4 className="font-semibold text-lg mb-1">Preview for: {selectedWell}</h4>
        {previewData ? (
          <pre className="bg-slate-100 p-3 rounded-md overflow-x-auto text-sm">
            {JSON.stringify(previewData, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-muted-foreground">No preview data available or loading...</p>
        )}
      </div>

      <div>
        <h4 className="font-semibold text-lg mb-1">Statistics for: {selectedWell}</h4>
        {statistics ? (
          <pre className="bg-slate-100 p-3 rounded-md overflow-x-auto text-sm">
            {JSON.stringify(statistics, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-muted-foreground">No statistics available or loading...</p>
        )}
      </div>
    </div>
  );
};
