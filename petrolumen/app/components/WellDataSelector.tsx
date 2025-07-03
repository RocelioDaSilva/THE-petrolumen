"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface WellDataSelectorProps {
  loadedWells: string[];
  selectedWell: string;
  onSelectedWellChange: (wellName: string) => void;
  onRefreshWells: () => void;
  isLoading: boolean;
}

export const WellDataSelector: React.FC<WellDataSelectorProps> = ({
  loadedWells,
  selectedWell,
  onSelectedWellChange,
  onRefreshWells,
  isLoading,
}) => {
  return (
    <div className="flex items-center space-x-2 mb-4">
      <Label htmlFor="wellSelect" className="whitespace-nowrap">Select Well: </Label>
      <Select
        value={selectedWell}
        onValueChange={onSelectedWellChange}
        disabled={isLoading || loadedWells.length === 0}
      >
        <SelectTrigger className="w-[280px]">
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
      <Button onClick={onRefreshWells} disabled={isLoading} variant="outline" size="sm">Refresh Well List</Button>
    </div>
  );
};
