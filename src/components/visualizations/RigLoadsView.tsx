import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield } from "lucide-react";
import * as RigLoads from "@/lib/drilling/rigLoads";

export const RigLoadsView: React.FC = () => {
  const [hookLoad, setHookLoad] = useState<number>(500000);
  const [numLines, setNumLines] = useState<number>(10);

  const res = RigLoads.calculateRigLoads(hookLoad, numLines);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Shield className="h-8 w-8 text-rose-600" />
        <div>
          <h1 className="text-2xl font-bold">Rig Loads & Derrick Capacity</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 7 Structural Safety</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Hoisting Load Inputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Hook Load (lb)</Label>
              <Input type="number" value={hookLoad} onChange={(e) => setHookLoad(Number(e.target.value))} />
            </div>
            <div>
              <Label>Lines Strung</Label>
              <Input type="number" value={numLines} onChange={(e) => setNumLines(Number(e.target.value))} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Calculated Structural & Fast Line Loads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="p-3 bg-slate-50 rounded-lg space-y-1">
              <p className="flex justify-between"><span>Dead Line Load:</span> <strong>{res.deadLineLoadLb.toLocaleString()} lb</strong></p>
              <p className="flex justify-between"><span>Fast Line Load (Static):</span> <strong>{res.fastLineLoadStaticLb.toLocaleString()} lb</strong></p>
              <p className="flex justify-between"><span>Fast Line Load (Dynamic Hoisting):</span> <strong className="text-rose-600">{res.fastLineLoadDynamicHoistingLb.toLocaleString()} lb</strong></p>
            </div>
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg space-y-1">
              <p className="flex justify-between font-semibold text-rose-900"><span>Total Derrick Load:</span> <strong>{res.derrickLoadLb.toLocaleString()} lb</strong></p>
              <p className="flex justify-between text-xs text-rose-700"><span>Fast Line Safety Factor:</span> <strong>{res.fastLineSafetyFactor1}</strong></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default RigLoadsView;
