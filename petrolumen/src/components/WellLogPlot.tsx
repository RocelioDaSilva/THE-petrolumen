'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { FileSpreadsheet, Upload, AlertCircle, RefreshCw, Layers, CheckCircle2 } from 'lucide-react';
import { parseLasFile, LasParseResponse } from '@/lib/backendClient';

interface WellLogPlotProps {
  wellId?: string;
  initialData?: LasParseResponse['data'] | null;
}

export function WellLogPlot({ wellId = 'WELL-001', initialData = null }: WellLogPlotProps) {
  const [file, setFile] = useState<File | null>(null);
  const [logData, setLogData] = useState<LasParseResponse['data'] | null>(initialData);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Depth range filtering
  const [depthRange, setDepthRange] = useState<[number, number]>([0, 10000]);
  const [showTrack1, setShowTrack1] = useState<boolean>(true);
  const [showTrack2, setShowTrack2] = useState<boolean>(true);
  const [showTrack3, setShowTrack3] = useState<boolean>(true);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadAndParse = async () => {
    if (!file) {
      setError('Please select a .las file to upload.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await parseLasFile(file);
      setLogData(res.data);
      if (res.data.summary) {
        const startD = typeof res.data.summary.start_depth === 'number' ? res.data.summary.start_depth : 0;
        const stopD = typeof res.data.summary.stop_depth === 'number' ? res.data.summary.stop_depth : 10000;
        setDepthRange([Math.min(startD, stopD), Math.max(startD, stopD)]);
      }
    } catch (err: any) {
      console.error('Failed to parse LAS file:', err);
      setError(err.message || 'Failed to parse LAS file. Ensure valid .las format.');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    if (file) {
      handleUploadAndParse();
    }
  };

  // Prepare chart records filtered by depth range
  const chartRecords = React.useMemo(() => {
    if (!logData || !logData.records) return [];

    return logData.records
      .filter((rec) => {
        const depthKey = Object.keys(rec).find((k) =>
          ['DEPTH', 'DEPT', 'DEP', 'depth', 'dept'].includes(k.toUpperCase())
        );
        const depthVal = depthKey ? Number(rec[depthKey]) : null;
        if (depthVal === null || isNaN(depthVal)) return true;
        return depthVal >= depthRange[0] && depthVal <= depthRange[1];
      })
      .map((rec) => {
        const depthKey = Object.keys(rec).find((k) =>
          ['DEPTH', 'DEPT', 'DEP', 'depth', 'dept'].includes(k.toUpperCase())
        );
        return {
          ...rec,
          DEPTH_DISPLAY: depthKey ? Number(rec[depthKey]) : 0,
        };
      });
  }, [logData, depthRange]);

  // Determine available curve keys
  const curveKeys = React.useMemo(() => {
    if (!logData || !logData.curves) return [];
    return Object.keys(logData.curves);
  }, [logData]);

  // Identify curves for tracks
  const track1Curves = curveKeys.filter((k) => ['GR', 'SGR', 'CALI', 'CAL', 'BS', 'SP'].some((kw) => k.includes(kw)));
  const track2Curves = curveKeys.filter((k) => ['ILD', 'ILM', 'LLD', 'LLS', 'RT', 'RES', 'SFL'].some((kw) => k.includes(kw)));
  const track3Curves = curveKeys.filter((k) => ['NPHI', 'RHOB', 'PHIE', 'PHIT', 'DT'].some((kw) => k.includes(kw)));

  // 1. Loading State
  if (loading) {
    return (
      <Card className="w-full shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary animate-pulse" />
            Parsing Well Log File...
          </CardTitle>
          <CardDescription>Reading LAS headers and curve arrays</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
          <Skeleton className="h-96 w-full" />
        </CardContent>
      </Card>
    );
  }

  // 2. Error State
  if (error && !logData) {
    return (
      <Card className="w-full border-rose-200 dark:border-rose-900 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-rose-600 dark:text-rose-400 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Well Log Ingestion Error
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertTitle>Failed to Parse File</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="flex gap-4">
            <Button onClick={handleRetry} variant="default" className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Try Again
            </Button>
            <Button
              onClick={() => {
                setError(null);
                setFile(null);
              }}
              variant="outline"
            >
              Select Different File
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // 3. Empty State
  if (!logData) {
    return (
      <Card className="w-full border-dashed border-2 shadow-sm">
        <CardHeader className="text-center">
          <div className="mx-auto bg-primary/10 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-2">
            <FileSpreadsheet className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">Upload LAS Well Log File</CardTitle>
          <CardDescription>
            Ingest Log ASCII Standard (.las) files to visualize multi-track well log curves (Gamma Ray, Resistivity, Porosity, Density).
          </CardDescription>
        </CardHeader>
        <CardContent className="max-w-md mx-auto space-y-4">
          <div className="space-y-2">
            <Label htmlFor="las-file-input">Select LAS File (.las)</Label>
            <Input
              id="las-file-input"
              type="file"
              accept=".las,.txt"
              onChange={handleFileChange}
            />
          </div>
          <Button
            onClick={handleUploadAndParse}
            disabled={!file}
            className="w-full flex items-center justify-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Parse & Visualize Log
          </Button>
        </CardContent>
      </Card>
    );
  }

  // 4. Success State
  return (
    <div className="space-y-6 w-full">
      {/* Well Header Summary Card */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-2xl font-bold flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                {logData.well_name || wellId}
              </CardTitle>
              <CardDescription className="mt-1">
                Field: {logData.metadata.FLD?.value || 'N/A'} | Company: {logData.metadata.COMP?.value || 'N/A'} | API: {logData.metadata.API?.value || 'N/A'}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setLogData(null);
                  setFile(null);
                }}
              >
                Upload Another Log
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-muted/30 p-4 rounded-lg">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Start Depth</p>
              <p className="text-lg font-bold">{logData.summary.start_depth}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Stop Depth</p>
              <p className="text-lg font-bold">{logData.summary.stop_depth}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Curve Count</p>
              <p className="text-lg font-bold">{logData.summary.curve_count}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-medium">Total Records</p>
              <p className="text-lg font-bold">{logData.summary.record_count}</p>
            </div>
          </div>

          {/* Curves Badges */}
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-xs font-semibold text-muted-foreground mr-2">Available Curves:</span>
            {curveKeys.map((c) => (
              <Badge key={c} variant="secondary" className="text-xs">
                {c} ({logData.curves[c]?.unit || 'dim'})
              </Badge>
            ))}
          </div>

          {/* Depth Range & Track Controls */}
          <div className="border-t pt-4 space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="space-y-1 w-full sm:w-1/2">
                <Label className="text-xs font-semibold">
                  Depth Range: {depthRange[0]} - {depthRange[1]}
                </Label>
                <Slider
                  min={Number(logData.summary.start_depth) || 0}
                  max={Number(logData.summary.stop_depth) || 10000}
                  step={10}
                  value={depthRange}
                  onValueChange={(val) => setDepthRange([val[0], val[1]])}
                />
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={showTrack1 ? 'default' : 'outline'}
                  onClick={() => setShowTrack1(!showTrack1)}
                >
                  Track 1 (Lithology)
                </Button>
                <Button
                  size="sm"
                  variant={showTrack2 ? 'default' : 'outline'}
                  onClick={() => setShowTrack2(!showTrack2)}
                >
                  Track 2 (Resistivity)
                </Button>
                <Button
                  size="sm"
                  variant={showTrack3 ? 'default' : 'outline'}
                  onClick={() => setShowTrack3(!showTrack3)}
                >
                  Track 3 (Porosity)
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Multi-Track Well Log Plot Card */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-bold">Multi-Track Well Log Interpretation Plot</CardTitle>
          <CardDescription>
            Interactive log track display plot. Depth increases vertically downwards.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Track 1: Lithology / GR */}
            {showTrack1 && (
              <div className="border rounded-lg p-4 space-y-2">
                <h4 className="text-sm font-bold text-center border-b pb-2 text-amber-600 dark:text-amber-400">
                  Track 1: Gamma Ray & Caliper
                </h4>
                <div className="h-96 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={chartRecords}
                      layout="vertical"
                      margin={{ top: 10, right: 10, left: 20, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis type="number" domain={[0, 'auto']} orientation="top" />
                      <YAxis
                        type="number"
                        dataKey="DEPTH_DISPLAY"
                        reversed
                        domain={['dataMin', 'dataMax']}
                        tickFormatter={(val) => `${val.toFixed(0)}m`}
                      />
                      <Tooltip />
                      <Legend />
                      {track1Curves.length > 0 ? (
                        track1Curves.map((ck, i) => (
                          <Line
                            key={ck}
                            type="monotone"
                            dataKey={ck}
                            name={`${ck} (${logData.curves[ck]?.unit || ''})`}
                            stroke={i === 0 ? '#d97706' : '#2563eb'}
                            strokeWidth={2}
                            dot={false}
                          />
                        ))
                      ) : (
                        <Line type="monotone" dataKey="GR" name="GR (API)" stroke="#d97706" strokeWidth={2} dot={false} />
                      )}
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Track 2: Resistivity */}
            {showTrack2 && (
              <div className="border rounded-lg p-4 space-y-2">
                <h4 className="text-sm font-bold text-center border-b pb-2 text-blue-600 dark:text-blue-400">
                  Track 2: Resistivity (ILD / RT)
                </h4>
                <div className="h-96 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={chartRecords}
                      layout="vertical"
                      margin={{ top: 10, right: 10, left: 20, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis type="number" domain={[0.1, 'auto']} orientation="top" />
                      <YAxis
                        type="number"
                        dataKey="DEPTH_DISPLAY"
                        reversed
                        domain={['dataMin', 'dataMax']}
                        tickFormatter={(val) => `${val.toFixed(0)}m`}
                      />
                      <Tooltip />
                      <Legend />
                      {track2Curves.length > 0 ? (
                        track2Curves.map((ck, i) => (
                          <Line
                            key={ck}
                            type="monotone"
                            dataKey={ck}
                            name={`${ck} (${logData.curves[ck]?.unit || 'ohmm'})`}
                            stroke={i === 0 ? '#2563eb' : '#059669'}
                            strokeWidth={2}
                            dot={false}
                          />
                        ))
                      ) : (
                        <Line type="monotone" dataKey="ILD" name="ILD (ohmm)" stroke="#2563eb" strokeWidth={2} dot={false} />
                      )}
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Track 3: Porosity & Density */}
            {showTrack3 && (
              <div className="border rounded-lg p-4 space-y-2">
                <h4 className="text-sm font-bold text-center border-b pb-2 text-emerald-600 dark:text-emerald-400">
                  Track 3: Porosity (NPHI) & Density (RHOB)
                </h4>
                <div className="h-96 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={chartRecords}
                      layout="vertical"
                      margin={{ top: 10, right: 10, left: 20, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis type="number" domain={['auto', 'auto']} orientation="top" />
                      <YAxis
                        type="number"
                        dataKey="DEPTH_DISPLAY"
                        reversed
                        domain={['dataMin', 'dataMax']}
                        tickFormatter={(val) => `${val.toFixed(0)}m`}
                      />
                      <Tooltip />
                      <Legend />
                      {track3Curves.length > 0 ? (
                        track3Curves.map((ck, i) => (
                          <Line
                            key={ck}
                            type="monotone"
                            dataKey={ck}
                            name={`${ck} (${logData.curves[ck]?.unit || ''})`}
                            stroke={i === 0 ? '#059669' : '#dc2626'}
                            strokeWidth={2}
                            dot={false}
                          />
                        ))
                      ) : (
                        <Line type="monotone" dataKey="NPHI" name="NPHI (v/v)" stroke="#059669" strokeWidth={2} dot={false} />
                      )}
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
