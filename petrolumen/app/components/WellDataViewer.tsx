"use client";

import React from 'react';
import { WellDataPreview, WellStatistics } from '@/lib/backendClient';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";

interface WellDataViewerProps {
  selectedWell: string | null;
  previewData: WellDataPreview[] | null;
  statistics: WellStatistics | null;
  isLoading: boolean; // To show loading state if data for selected well is being fetched
}

const renderStatisticValue = (value: unknown, isNumericDetail: boolean = false): React.ReactNode => {
  if (typeof value === 'number') {
    return <span className="text-slate-700 dark:text-slate-200">{value.toFixed(isNumericDetail ? 4 : 2)}</span>;
  }
  if (typeof value === 'boolean') {
    return <span className="text-slate-700 dark:text-slate-200">{value ? 'True' : 'False'}</span>;
  }
  if (typeof value === 'object' && value !== null) {
    if (Array.isArray(value)) {
      return <pre className="text-xs bg-slate-100 dark:bg-slate-800 p-2 rounded overflow-x-auto">{JSON.stringify(value, null, 2)}</pre>;
    }
    // For nested objects, display as key-value pairs
    return (
      <div className="space-y-1 mt-1">
        {Object.entries(value).map(([key, val]) => (
          <div key={key} className="flex justify-between text-xs">
            <span className="font-medium text-slate-500 dark:text-slate-400 capitalize">{key.replace(/_/g, ' ')}:</span>
            {renderStatisticValue(val, isNumericDetail)}
          </div>
        ))}
      </div>
    );
  }
  return <span className="text-slate-700 dark:text-slate-200">{String(value)}</span>;
};


export const WellDataViewer: React.FC<WellDataViewerProps> = ({
  selectedWell,
  previewData,
  statistics,
  isLoading,
}) => {
  if (!selectedWell) {
    return <p className="text-sm text-muted-foreground py-4">Please select a well to view its data.</p>;
  }

  if (isLoading) {
    return (
      <div className="space-y-6 py-4">
        <div>
          <Skeleton className="h-6 w-1/2 mb-2" />
          <Skeleton className="h-4 w-3/4 mb-4" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        </div>
        <div>
          <Skeleton className="h-6 w-1/2 mb-2" />
          <Skeleton className="h-4 w-3/4 mb-4" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  const previewColumns = previewData && previewData.length > 0 ? Object.keys(previewData[0]) : [];

  return (
    <div className="space-y-6 mt-4">
      <Card>
        <CardHeader>
          <CardTitle>Data Preview for: {selectedWell}</CardTitle>
          <CardDescription>First few rows of the well data.</CardDescription>
        </CardHeader>
        <CardContent>
          {previewData && previewData.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  {previewColumns.map((key) => (
                    <TableHead key={key}>{key}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {previewData.map((row, rowIndex) => (
                  <TableRow key={rowIndex}>
                    {previewColumns.map((colKey) => (
                      // TODO: Implement richer display formatting for different data types in table cells if needed
                      // For example, boolean values, specific number precisions, date formats etc.
                      // Current implementation uses renderStatisticValue which has some basic type handling.
                      <TableCell key={`${rowIndex}-${colKey}`}>{renderStatisticValue(row[colKey])}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">No preview data available for this well.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Statistics for: {selectedWell}</CardTitle>
          <CardDescription>Summary statistics of the well data.</CardDescription>
        </CardHeader>
        <CardContent>
          {statistics ? (
            <Accordion type="single" collapsible className="w-full">
              {Object.entries(statistics).map(([key, value]) => {
                if (key === 'description' && typeof value === 'object' && value !== null) {
                  return (
                    <AccordionItem value="description" key="description">
                      <AccordionTrigger className="text-base font-semibold">Data Description (Per Column)</AccordionTrigger>
                      <AccordionContent>
                        <Accordion type="multiple" collapsible className="w-full space-y-2">
                          {Object.entries(value).map(([colName, colStats]) => (
                            <AccordionItem value={`desc-${colName}`} key={`desc-${colName}`}>
                              <AccordionTrigger className="text-sm font-medium">{colName}</AccordionTrigger>
                              <AccordionContent className="pl-4">
                                {typeof colStats === 'object' && colStats !== null ? (
                                   <div className="space-y-1 py-2">
                                   {Object.entries(colStats).map(([statKey, statVal]) => (
                                     <div key={statKey} className="flex justify-between text-xs">
                                       <span className="font-medium text-slate-500 dark:text-slate-400 capitalize">{statKey.replace(/_/g, ' ')}:</span>
                                       {/* Pass true for isNumericDetail for the 'description' section */}
                                       {renderStatisticValue(statVal, true)}
                                     </div>
                                   ))}
                                 </div>
                                ) : (
                                  <p className="text-xs text-muted-foreground">{String(colStats)}</p>
                                )}
                              </AccordionContent>
                            </AccordionItem>
                          ))}
                        </Accordion>
                      </AccordionContent>
                    </AccordionItem>
                  );
                }
                // Handle other top-level statistics
                return (
                  <AccordionItem value={key} key={key}>
                    <AccordionTrigger className="text-base font-semibold capitalize">{key.replace(/_/g, ' ')}</AccordionTrigger>
                    <AccordionContent className="pl-4 py-2">
                      {/* Pass false or default for isNumericDetail for general statistics */}
                      {renderStatisticValue(value, false)}
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          ) : (
            <p className="text-sm text-muted-foreground">No statistics available for this well.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
