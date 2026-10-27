import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Gauge } from "lucide-react";
import * as RigOps from "@/lib/drilling/rigOperations";

export const RigOperationsView: React.FC = () => {
  const [slugVol, setSlugVol] = useState<number>(20);
  const [mwPpg, setMwPpg] = useState<number>(10.0);
  const [slugMwPpg, setSlugMwPpg] = useState<number>(12.0);

  const acc = RigOps.accumulatorUsableVolume(1000, 3000, 1200, 20);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Gauge className="h-8 w-8 text-teal-600" />
        <div>
          <h1 className="text-2xl font-bold">Rig Operations Toolkit</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 2 Rig Calculations</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Accumulator Unit Usable Fluid</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg space-y-2 text-sm">
              <p className="flex justify-between"><span>20-Gal Bottle Usable Fluid:</span> <strong className="text-teal-900 text-lg">{acc.usableVolumeGal} Gal</strong></p>
              <p className="flex justify-between text-xs text-teal-700"><span>Usable Fraction:</span> <strong>{acc.usableFraction * 100}%</strong></p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Heavy Slug Dry Pipe Calculations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Current MW (ppg)</Label>
                <Input type="number" value={mwPpg} onChange={(e) => setMwPpg(Number(e.target.value))} />
              </div>
              <div>
                <Label>Slug MW (ppg)</Label>
                <Input type="number" value={slugMwPpg} onChange={(e) => setSlugMwPpg(Number(e.target.value))} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default RigOperationsView;
