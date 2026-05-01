"use client";

import React from "react";
import { useAppStore } from "@/stores/appStore";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw } from "lucide-react";

interface WellDataSelectorProps {
  loadedWells: string[];
  onRefreshWells: () => void;
  isLoading: boolean;
}

export const WellDataSelector: React.FC<WellDataSelectorProps> = ({
  loadedWells,
  onRefreshWells,
  isLoading,
}) => {
  const { selectedWell, setSelectedWell } = useAppStore();

  return (
    <div className="flex flex-col sm:flex-row items-end gap-4 mb-6">
      <div className="grid gap-2 flex-1 w-full">
        <label htmlFor="well-select" className="text-sm font-medium">
          Select Well
        </label>
        <Select
          value={selectedWell || ""}
          onValueChange={(value) => setSelectedWell(value === "" ? null : value)}
          disabled={isLoading || loadedWells.length === 0}
        >
          <SelectTrigger id="well-select">
            <SelectValue placeholder={loadedWells.length === 0 ? "No wells loaded" : "Select a well"} />
          </SelectTrigger>
          <SelectContent>
            {loadedWells.map((well) => (
              <SelectItem key={well} value={well}>
                {well}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button
        variant="outline"
        size="icon"
        onClick={onRefreshWells}
        disabled={isLoading}
        title="Refresh well list"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
      </Button>
    </div>
  );
};
