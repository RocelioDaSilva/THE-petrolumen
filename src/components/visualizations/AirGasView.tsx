import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Wind } from "lucide-react";
import * as AirGas from "@/lib/drilling/airGas";

export const AirGasView: React.FC = () => {
  const [pSurface, setPSurface] = useState<number>(2000);
  const [sg, setSg] = useState<number>(0.65);
  const [depth, setDepth] = useState<number>(10000);

  const res = AirGas.staticGasColumnBHP(pSurface, sg, depth);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Wind className="h-8 w-8 text-sky-600" />
        <div>
          <h1 className="text-2xl font-bold">Air & Gas Drilling Toolkit</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 8 Compressible Circulation</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Gas Column Inputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Surface Pressure (psia)</Label>
                <Input type="number" value={pSurface} onChange={(e) => setPSurface(Number(e.target.value))} />
              </div>
              <div>
                <Label>Gas Specific Gravity</Label>
                <Input type="number" value={sg} onChange={(e) => setSg(Number(e.target.value))} />
              </div>
              <div className="col-span-2">
                <Label>Depth (ft)</Label>
                <Input type="number" value={depth} onChange={(e) => setDepth(Number(e.target.value))} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Calculated Bottom Hole Pressures</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-sky-50 border border-sky-200 rounded-lg space-y-2">
              <p className="flex justify-between text-sm"><span>Static Bottom Hole Pressure (Psia):</span> <strong className="text-sky-900 text-lg">{res.bottomHolePressurePsia} psia</strong></p>
              <p className="flex justify-between text-sm"><span>Static Bottom Hole Pressure (Psig):</span> <strong className="text-sky-800">{res.bottomHolePressurePsig} psig</strong></p>
              <p className="flex justify-between text-sm"><span>Static Bottom Hole Pressure (Bar):</span> <strong className="text-sky-800">{res.bottomHolePressureBar} bar</strong></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default AirGasView;
