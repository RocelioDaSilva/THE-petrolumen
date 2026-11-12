import { useCallback, useEffect, useState } from "react";
import { Clock3, Database, LoaderCircle, LogIn, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchSavedSimulation,
  fetchSavedSimulations,
  removeSavedSimulation,
  SavedSimulation,
  SavedSimulationSummary,
} from "@/lib/api";
import { useAuth } from "@/lib/authContext";

interface SavedRunsPanelProps {
  onLoad: (run: SavedSimulation) => boolean;
}

export default function SavedRunsPanel({ onLoad }: SavedRunsPanelProps) {
  const { user, openAuthDialog } = useAuth();
  const [runs, setRuns] = useState<SavedSimulationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeRunId, setActiveRunId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!user) {
      setRuns([]);
      setError("");
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      setRuns(await fetchSavedSimulations());
    } catch (requestError) {
      setError(getApiError(requestError));
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleLoad = async (id: number) => {
    setActiveRunId(id);
    setError("");
    try {
      const loaded = await fetchSavedSimulation(id);
      if (!onLoad(loaded)) {
        setError(`Loading "${loaded.simulation_type}" runs is not supported in the current UI yet.`);
      }
    } catch (requestError) {
      setError(getApiError(requestError));
    } finally {
      setActiveRunId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this saved run? This action cannot be undone.")) return;
    setActiveRunId(id);
    setError("");
    try {
      await removeSavedSimulation(id);
      setRuns((current) => current.filter((run) => run.id !== id));
    } catch (requestError) {
      setError(getApiError(requestError));
    } finally {
      setActiveRunId(null);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Database className="h-4 w-4 text-primary" />
            My Saved Runs
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Reopen saved calculation inputs and results.
          </p>
        </div>
        {user && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => void refresh()}
            disabled={isLoading}
            className="h-8 w-8"
            aria-label="Refresh saved runs"
            title="Refresh saved runs"
          >
            {isLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-5">
        {!user ? (
          <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
            <p className="text-xs text-muted-foreground">
              Sign in to save, load, and manage your runs.
            </p>
            <Button size="sm" onClick={openAuthDialog} className="gap-2">
              <LogIn className="h-3.5 w-3.5" />
              Sign in
            </Button>
          </div>
        ) : isLoading && runs.length === 0 ? (
          <div role="status" className="flex items-center gap-2 py-4 text-xs text-muted-foreground">
            <LoaderCircle className="h-4 w-4 animate-spin text-primary" />
            Loading saved runs...
          </div>
        ) : error && runs.length === 0 ? (
          <div className="space-y-3">
            <p role="alert" className="text-xs text-destructive">{error}</p>
            <Button variant="outline" size="sm" onClick={() => void refresh()}>Try again</Button>
          </div>
        ) : runs.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border px-4 py-6 text-center">
            <Clock3 className="mx-auto h-5 w-5 text-muted-foreground" />
            <p className="mt-2 text-xs font-medium">No saved runs yet</p>
            <p className="mt-1 text-[11px] text-muted-foreground">
              Run a reservoir simulation and save it to see it here.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
            {runs.map((run) => (
              <div
                key={run.id}
                className="flex flex-col justify-between gap-3 rounded-lg border border-border bg-background/40 p-3 sm:flex-row sm:items-center"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{run.name}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className="font-mono text-[9px]">{run.simulation_type}</Badge>
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(run.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void handleLoad(run.id)}
                    disabled={activeRunId !== null}
                  >
                    {activeRunId === run.id ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : "Load"}
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => void handleDelete(run.id)}
                    disabled={activeRunId !== null}
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    aria-label={`Delete ${run.name}`}
                    title="Delete saved run"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function getApiError(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "detail" in error &&
    typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The saved-runs request failed.";
}
