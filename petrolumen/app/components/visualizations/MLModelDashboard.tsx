"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  trainWellAIModels,
  AITrainResponse,
  getWellStatistics,
  WellStatistics,
} from "@/lib/backendClient";
import { Loader2, Brain, CheckCircle2, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface MLModelDashboardProps {
  wellName: string;
}

const MLModelDashboard: React.FC<MLModelDashboardProps> = ({ wellName }) => {
  const [stats, setStats] = useState<WellStatistics | null>(null);
  const [targetColumn, setTargetColumn] = useState<string>("oil_rate");
  const [featureColumns, setFeatureColumns] = useState<string[]>(["days_from_start"]);
  const [training, setTraining] = useState<boolean>(false);
  const [result, setResult] = useState<AITrainResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      if (!wellName) return;
      try {
        const data = await getWellStatistics(wellName);
        setStats(data);
        // Reset state when well changes
        setResult(null);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch stats for ML:", err);
      }
    };
    fetchStats();
  }, [wellName]);

  const handleTrain = async () => {
    if (!wellName || !targetColumn || featureColumns.length === 0) return;
    setTraining(true);
    setResult(null);
    setError(null);
    try {
      const res = await trainWellAIModels(wellName, targetColumn, featureColumns);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to train models");
    } finally {
      setTraining(false);
    }
  };

  const toggleFeature = (col: string) => {
    setFeatureColumns((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  };

  if (!wellName) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Select a well to configure AI models.
      </div>
    );
  }

  const columns = stats ? Object.keys(stats).filter(c => c !== 'message') : [];
  // Add 'days_from_start' as a virtual feature if it's not in columns (it's created on backend)
  const availableFeatures = [...columns];
  if (!availableFeatures.includes('days_from_start')) {
      availableFeatures.push('days_from_start');
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          <CardTitle>Machine Learning: {wellName}</CardTitle>
        </div>
        <CardDescription>
          Train AI models (SVR, XGBoost) to predict well performance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <Label className="text-base font-semibold">Target Column</Label>
              <p className="text-sm text-muted-foreground mb-2">
                What do you want to predict?
              </p>
              <Select value={targetColumn} onValueChange={setTargetColumn}>
                <SelectTrigger>
                  <SelectValue placeholder="Select target" />
                </SelectTrigger>
                <SelectContent>
                  {columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-base font-semibold">Feature Columns</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Predictors to use for the model
              </p>
              <div className="grid grid-cols-2 gap-2">
                {availableFeatures.map((col) => (
                  <div key={col} className="flex items-center space-x-2">
                    <Checkbox
                      id={`feat-${col}`}
                      checked={featureColumns.includes(col)}
                      onCheckedChange={() => toggleFeature(col)}
                      disabled={col === targetColumn}
                    />
                    <label
                      htmlFor={`feat-${col}`}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {col}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <Button
              onClick={handleTrain}
              disabled={training || featureColumns.length === 0}
              className="w-full"
            >
              {training ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Training Models...
                </>
              ) : (
                "Start Training"
              )}
            </Button>
          </div>

          <div className="border rounded-lg p-4 bg-muted/30 min-h-[200px] flex flex-col">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              Status & Results
            </h3>

            {!result && !error && !training && (
                <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
                    <Brain className="h-10 w-10 mb-2 opacity-20" />
                    <p>Configure and start training to see results</p>
                </div>
            )}

            {training && (
                <div className="flex-1 flex flex-col items-center justify-center">
                    <Loader2 className="h-10 w-10 animate-spin text-primary mb-2" />
                    <p className="animate-pulse font-medium">Processing hyperparameter tuning...</p>
                </div>
            )}

            {error && (
                <div className="flex-1 flex flex-col items-center justify-center text-destructive">
                    <AlertCircle className="h-10 w-10 mb-2" />
                    <p className="font-medium">Training Error</p>
                    <p className="text-xs text-center">{error}</p>
                </div>
            )}

            {result && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                  <p className="font-medium">Training Complete!</p>
                </div>

                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Best Model:</span>
                        <Badge variant="default" className="uppercase">{result.best_model}</Badge>
                    </div>

                    <div className="space-y-2">
                        {result.performance && Object.entries(result.performance).map(([name, perf]) => (
                            <div key={name} className="bg-background border rounded-md p-2 text-sm">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-bold uppercase">{name}</span>
                                    {name === result.best_model && <span className="text-[10px] bg-green-100 text-green-700 px-1 rounded">BEST</span>}
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div>R² Score: <span className="font-mono">{perf.r2.toFixed(4)}</span></div>
                                    <div>RMSE: <span className="font-mono">{perf.rmse.toFixed(2)}</span></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MLModelDashboard;
