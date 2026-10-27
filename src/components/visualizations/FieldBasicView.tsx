import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Calculator, Compass } from "lucide-react";
import * as FieldBasic from "@/lib/field/basic";

export const FieldBasicView: React.FC = () => {
  const [mwPpg, setMwPpg] = useState<number>(10.0);
  const [hFt, setHFt] = useState<number>(10000);
  const [dl, setDl] = useState<number>(6.5);
  const [stroke, setStroke] = useState<number>(12);
  const [spm, setSpm] = useState<number>(100);
  const [dh, setDh] = useState<number>(8.5);
  const [dp, setDp] = useState<number>(4.5);

  const hpPsi = FieldBasic.hydrostaticPressure_psi_ppg(mwPpg, hFt);
  const pGrad = FieldBasic.pressureGradient_psi_ft(mwPpg);
  const triplexGpm = FieldBasic.triplex_gpm(dl, stroke, spm, 0.95);
  const annCap = FieldBasic.annularCapacity_bblFt(dh, dp);
  const av = FieldBasic.annularVelocity_ftMin_gpm(triplexGpm, dh, dp);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Calculator className="h-8 w-8 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold">Field Operations Quick Reference</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 1 Field Formulas</p>
        </div>
      </div>

      <Tabs defaultValue="formulas" className="w-full">
        <TabsList>
          <TabsTrigger value="formulas">Field Formulas</TabsTrigger>
          <TabsTrigger value="conversions">Unit Conversions</TabsTrigger>
        </TabsList>

        <TabsContent value="formulas" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Hydrostatics & Pressures</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Mud Weight (ppg)</Label>
                    <Input type="number" value={mwPpg} onChange={(e) => setMwPpg(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label>Depth (ft)</Label>
                    <Input type="number" value={hFt} onChange={(e) => setHFt(Number(e.target.value))} />
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
                  <p className="flex justify-between"><span>Hydrostatic Pressure:</span> <strong className="text-blue-600">{Math.round(hpPsi)} psi</strong></p>
                  <p className="flex justify-between"><span>Pressure Gradient:</span> <strong>{pGrad.toFixed(3)} psi/ft</strong></p>
                  <p className="flex justify-between"><span>Equivalent Density:</span> <strong>{(FieldBasic.sgFromMudWeight(mwPpg)).toFixed(2)} SG</strong></p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Pump & Hydraulics Output</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <Label>Liner (in)</Label>
                    <Input type="number" value={dl} onChange={(e) => setDl(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label>Stroke (in)</Label>
                    <Input type="number" value={stroke} onChange={(e) => setStroke(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label>SPM</Label>
                    <Input type="number" value={spm} onChange={(e) => setSpm(Number(e.target.value))} />
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
                  <p className="flex justify-between"><span>Flow Rate:</span> <strong className="text-blue-600">{Math.round(triplexGpm)} gpm</strong></p>
                  <p className="flex justify-between"><span>Pump Output:</span> <strong>{FieldBasic.triplex_bblPerStroke(dl, stroke, 0.95).toFixed(4)} bbl/stk</strong></p>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="text-lg">Annular Hydraulics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Hole / Casing ID (in)</Label>
                    <Input type="number" value={dh} onChange={(e) => setDh(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label>Pipe OD (in)</Label>
                    <Input type="number" value={dp} onChange={(e) => setDp(Number(e.target.value))} />
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm grid grid-cols-2 gap-4">
                  <div>
                    <p className="flex justify-between"><span>Annular Capacity:</span> <strong>{annCap.toFixed(4)} bbl/ft</strong></p>
                    <p className="flex justify-between"><span>Annular Capacity:</span> <strong>{(annCap * 42).toFixed(2)} gal/ft</strong></p>
                  </div>
                  <div>
                    <p className="flex justify-between"><span>Annular Velocity:</span> <strong className="text-blue-600">{Math.round(av)} ft/min</strong></p>
                    <p className="flex justify-between"><span>Bottoms-Up Time (10k ft):</span> <strong>{FieldBasic.bottomsUpTime(dh, dp, 10000, triplexGpm).toFixed(1)} min</strong></p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="conversions" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Compass className="h-5 w-5 text-blue-600" />
                <span>Field Unit Conversion Matrix (Appendix B)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="font-semibold text-gray-700">Density</p>
                  <p className="text-gray-500 mt-1">1 ppg = 0.1198 g/cm³</p>
                  <p className="text-gray-500">1 ppg = 7.4805 lb/ft³</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="font-semibold text-gray-700">Pressure</p>
                  <p className="text-gray-500 mt-1">1 psi = 0.06895 bar</p>
                  <p className="text-gray-500">1 psi = 6.8947 kPa</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="font-semibold text-gray-700">Volume</p>
                  <p className="text-gray-500 mt-1">1 bbl = 42 gal</p>
                  <p className="text-gray-500">1 bbl = 5.6146 ft³</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="font-semibold text-gray-700">Temperature</p>
                  <p className="text-gray-500 mt-1">°F = (°C × 1.8) + 32</p>
                  <p className="text-gray-500">°R = °F + 459.67</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
export default FieldBasicView;
