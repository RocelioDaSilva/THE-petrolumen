import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Container } from "lucide-react";
import * as TankCapacity from "@/lib/facilities/tankCapacity";

export const TankCapacityView: React.FC = () => {
  const [length, setLength] = useState<number>(30);
  const [width, setWidth] = useState<number>(10);
  const [height, setHeight] = useState<number>(8);
  const [depth, setDepth] = useState<number>(5);

  const rect = TankCapacity.rectangularTankCapacity(length, width, height, depth);
  const horiz = TankCapacity.horizontalCylindricalTankCapacity(height, length, depth);
  const vert = TankCapacity.verticalCylindricalTankCapacity(width, height, depth);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center space-x-3">
        <Container className="h-8 w-8 text-cyan-600" />
        <div>
          <h1 className="text-2xl font-bold">Tank Capacity Calculator</h1>
          <p className="text-gray-500 text-sm">Carter, Lyons & Lapeyrouse 5th Ed. Appendix A Geometry Sizing</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Tank Dimensions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Length / Height (ft)</Label>
                <Input type="number" value={length} onChange={(e) => setLength(Number(e.target.value))} />
              </div>
              <div>
                <Label>Width / Diameter (ft)</Label>
                <Input type="number" value={width} onChange={(e) => setWidth(Number(e.target.value))} />
              </div>
              <div>
                <Label>Tank Height / Diameter (ft)</Label>
                <Input type="number" value={height} onChange={(e) => setHeight(Number(e.target.value))} />
              </div>
              <div>
                <Label>Fluid Depth (ft)</Label>
                <Input type="number" value={depth} onChange={(e) => setDepth(Number(e.target.value))} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Calculated Tank Capacities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="p-3 bg-slate-50 rounded-lg space-y-1">
              <p className="font-semibold text-gray-700">Rectangular Flat Tank:</p>
              <p className="flex justify-between"><span>Total Volume:</span> <strong>{rect.totalBbl} bbl</strong></p>
              <p className="flex justify-between"><span>Partial Fluid Volume:</span> <strong className="text-cyan-600">{rect.partialBbl} bbl</strong></p>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg space-y-1">
              <p className="font-semibold text-gray-700">Horizontal Cylindrical Tank:</p>
              <p className="flex justify-between"><span>Total Volume:</span> <strong>{horiz.totalBbl} bbl</strong></p>
              <p className="flex justify-between"><span>Partial Fluid Volume:</span> <strong className="text-cyan-600">{horiz.partialBbl} bbl</strong></p>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg space-y-1">
              <p className="font-semibold text-gray-700">Vertical Cylindrical Tank:</p>
              <p className="flex justify-between"><span>Total Volume:</span> <strong>{vert.totalBbl} bbl</strong></p>
              <p className="flex justify-between"><span>Partial Fluid Volume:</span> <strong className="text-cyan-600">{vert.partialBbl} bbl</strong></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default TankCapacityView;
