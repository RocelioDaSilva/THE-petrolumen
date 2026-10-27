import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Activity, RotateCcw } from "lucide-react";
import * as TonMiles from "@/lib/drilling/tonMiles";

export const TonMilesView: React.FC = () => {
  const [depth, setDepth] = useState<number>(10000);
  const [standLength, setStandLength] = useState<number>(90);
  const [dpWeight, setDpWeight] = useState<number>(19.5);
  const [dcWeight, setDcWeight] = useState<number>(120);
  const [dcLength, setDcLength] = useState<number>(500);
  const [blockWeight, setBlockWeight] = useState<number>(25000);

  const [cumulativeTM, setCumulativeTM] = useState<number>(() => {
    const saved = localStorage.getItem("petrolumen_cumulative_ton_miles");
    return saved ? parseFloat(saved) : 420.0;
  });

  useEffect(() => {
    localStorage.setItem("petrolumen_cumulative_ton_miles", cumulativeTM.toString());
  }, [cumulativeTM]);

  const rttm = TonMiles.roundTripTonMiles(depth, standLength, dpWeight, dcWeight, dcLength, blockWeight);

  const handleAddTonMiles = () => {
    setCumulativeTM((prev) => Math.round((prev + rttm) * 10) / 10);
  };

  const handleReset = () => {
    setCumulativeTM(0);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Activity className="h-8 w-8 text-indigo-600" />
        <div>
          <h1 className="text-2xl font-bold">Ton-Mile & Cutoff Service Management</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 7 Wireline Care</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Operation Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Depth (ft)</Label>
                <Input type="number" value={depth} onChange={(e) => setDepth(Number(e.target.value))} />
              </div>
              <div>
                <Label>Stand Length (ft)</Label>
                <Input type="number" value={standLength} onChange={(e) => setStandLength(Number(e.target.value))} />
              </div>
              <div>
                <Label>DP Weight (lb/ft)</Label>
                <Input type="number" value={dpWeight} onChange={(e) => setDpWeight(Number(e.target.value))} />
              </div>
              <div>
                <Label>DC Weight (lb/ft)</Label>
                <Input type="number" value={dcWeight} onChange={(e) => setDcWeight(Number(e.target.value))} />
              </div>
              <div>
                <Label>DC Length (ft)</Label>
                <Input type="number" value={dcLength} onChange={(e) => setDcLength(Number(e.target.value))} />
              </div>
              <div>
                <Label>Block Weight (lb)</Label>
                <Input type="number" value={blockWeight} onChange={(e) => setBlockWeight(Number(e.target.value))} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="text-lg">Ton-Mile Calculations & Service Record</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-lg space-y-2">
              <p className="text-sm font-semibold text-indigo-800">Round Trip Ton-Miles (RTTM):</p>
              <p className="text-3xl font-bold text-indigo-950">{rttm} Ton-Miles</p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold">Cumulative Wireline Service:</span>
                <strong className="text-xl text-slate-800">{cumulativeTM} Ton-Miles</strong>
              </div>
              <p className="text-xs text-gray-500">Service Goal (1-1/4" Line): 1,350 Ton-Miles ({Math.max(0, 1350 - cumulativeTM)} TM remaining to cutoff)</p>
            </div>

            <div className="flex space-x-3">
              <Button onClick={handleAddTonMiles} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
                Record Trip (+{rttm} TM)
              </Button>
              <Button onClick={handleReset} variant="outline" className="flex items-center space-x-1">
                <RotateCcw className="h-4 w-4" />
                <span>Reset</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default TonMilesView;
