import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Layers } from "lucide-react";
import * as Core from "@/lib/drilling/coreAnalysis";
import * as Completions from "@/lib/drilling/completions";

export const CompletionsView: React.FC = () => {
  const [coreVol, setCoreVol] = useState<number>(25.7);
  const [waterExt, setWaterExt] = useState<number>(1.8);
  const [oilExt, setOilExt] = useState<number>(6.12);

  const core = Core.deanStarkCoreAnalysis(coreVol, waterExt, oilExt);
  const stretch = Completions.tubingStretchComponents(10000, 6.5, 2.875, 2.441, 3000, 1000, 50);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Layers className="h-8 w-8 text-emerald-600" />
        <div>
          <h1 className="text-2xl font-bold">Completions & Core Analysis Toolkit</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 7 Field Evaluation</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Dean Stark Core Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label>Core Vol (cm³)</Label>
                <Input type="number" value={coreVol} onChange={(e) => setCoreVol(Number(e.target.value))} />
              </div>
              <div>
                <Label>Water (cm³)</Label>
                <Input type="number" value={waterExt} onChange={(e) => setWaterExt(Number(e.target.value))} />
              </div>
              <div>
                <Label>Oil Mass (g)</Label>
                <Input type="number" value={oilExt} onChange={(e) => setOilExt(Number(e.target.value))} />
              </div>
            </div>
            <div className="p-4 bg-emerald-50 rounded-lg space-y-2 text-sm">
              <p className="flex justify-between"><span>Porosity (φ):</span> <strong className="text-emerald-700">{core.porosityPct}%</strong></p>
              <p className="flex justify-between"><span>Water Saturation (Sw):</span> <strong>{core.waterSaturationPct}%</strong></p>
              <p className="flex justify-between"><span>Oil Saturation (So):</span> <strong>{core.oilSaturationPct}%</strong></p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Tubing Stretch (10k ft String)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
              <p className="flex justify-between"><span>Weight Stretch:</span> <strong>{stretch.weightStretchFt} ft</strong></p>
              <p className="flex justify-between"><span>Temp Stretch:</span> <strong>{stretch.temperatureStretchFt} ft</strong></p>
              <p className="flex justify-between"><span>Pressure Stretch:</span> <strong>{stretch.pressureStretchFt} ft</strong></p>
              <p className="flex justify-between"><span>Total Tubing Stretch:</span> <strong className="text-emerald-600 text-lg">{stretch.totalStretchFt} ft</strong></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default CompletionsView;
