import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Anchor, AlertCircle } from "lucide-react";
import * as StuckPipe from "@/lib/drilling/stuckPipe";

export const StuckPipeView: React.FC = () => {
  const [fishVal, setFishVal] = useState<number>(100000);
  const [rigRate, setRigRate] = useState<number>(10000);
  const [stretch, setStretch] = useState<number>(24);
  const [overpull, setOverpull] = useState<number>(50000);
  const [dpWeight, setDpWeight] = useState<number>(19.5);

  const fq = StuckPipe.daysToQuitFishing(fishVal, rigRate);
  const fp1 = StuckPipe.freePointMethod1(stretch, overpull, dpWeight);
  const fFree = StuckPipe.forceToFreePipe(100, 1000, 0.2, 5.0);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Anchor className="h-8 w-8 text-amber-600" />
        <div>
          <h1 className="text-2xl font-bold">Stuck Pipe & Fishing Toolkit</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Chapter 2 Decision Tools</p>
        </div>
      </div>

      <Tabs defaultValue="economics" className="w-full">
        <TabsList>
          <TabsTrigger value="economics">Fishing Economics</TabsTrigger>
          <TabsTrigger value="freepoint">Free Point Analysis</TabsTrigger>
          <TabsTrigger value="forcetofree">Force to Free</TabsTrigger>
        </TabsList>

        <TabsContent value="economics" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Fishing Economics (Days to Quit)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Fish Value ($)</Label>
                  <Input type="number" value={fishVal} onChange={(e) => setFishVal(Number(e.target.value))} />
                </div>
                <div>
                  <Label>Daily Rig Rate ($/day)</Label>
                  <Input type="number" value={rigRate} onChange={(e) => setRigRate(Number(e.target.value))} />
                </div>
              </div>
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
                <p className="text-sm font-semibold text-amber-800 flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4" />
                  <span>Break-Even Days to Quit Fishing:</span>
                </p>
                <p className="text-3xl font-bold text-amber-900">{fq.daysToQuit} Days</p>
                <p className="text-xs text-amber-700">If fishing operations exceed {fq.daysToQuit} days, sidetracking or abandoning the fish becomes economically optimal.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="freepoint" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Free Point Determination</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Stretch (in)</Label>
                  <Input type="number" value={stretch} onChange={(e) => setStretch(Number(e.target.value))} />
                </div>
                <div>
                  <Label>Overpull (lb)</Label>
                  <Input type="number" value={overpull} onChange={(e) => setOverpull(Number(e.target.value))} />
                </div>
                <div>
                  <Label>DP Weight (lb/ft)</Label>
                  <Input type="number" value={dpWeight} onChange={(e) => setDpWeight(Number(e.target.value))} />
                </div>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
                <p className="flex justify-between"><span>Calculated Free Point Depth:</span> <strong className="text-amber-600 text-lg">{fp1} ft</strong></p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="forcetofree" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Differential Sticking & Force to Free</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
                <p className="flex justify-between"><span>Estimated Pull Force Required to Free Pipe:</span> <strong className="text-amber-600 text-lg">{fFree.toLocaleString()} lb</strong></p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
export default StuckPipeView;
