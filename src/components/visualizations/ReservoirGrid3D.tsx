import React, { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layers, Eye, RefreshCw, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface Cell3D {
  x: number;
  y: number;
  z: number;
  porosity: number;
  permX: number;
  pressure: number;
  waterSat: number;
  netToGross: number;
}

export default function ReservoirGrid3D() {
  const [property, setProperty] = useState<"porosity" | "permX" | "pressure" | "waterSat" | "netToGross">("porosity");
  const [selectedLayerZ, setSelectedLayerZ] = useState<number>(0);
  const [selectedCell, setSelectedCell] = useState<Cell3D | null>(null);
  const [rotationAngle, setRotationAngle] = useState(30);
  const [tiltAngle, setTiltAngle] = useState(55);
  const [zoom, setZoom] = useState(1);

  // Generate a realistic 8x8x4 reservoir grid (256 blocks)
  const gridCells = useMemo(() => {
    const cells: Cell3D[] = [];
    const nx = 8;
    const ny = 8;
    const nz = 4;

    for (let z = 0; z < nz; z++) {
      for (let y = 0; y < ny; y++) {
        for (let x = 0; x < nx; x++) {
          // Channelized porosity variation
          const channel = Math.sin((x / nx) * Math.PI) * Math.cos((y / ny) * Math.PI);
          const basePhi = 0.12 + 0.16 * Math.max(0, channel) + ((x * y) % 5) * 0.01;
          const porosity = Math.min(0.32, Math.max(0.06, basePhi - z * 0.015));
          const permX = Math.round(Math.pow(10, 1 + porosity * 8) * (1 - z * 0.15));
          const pressure = Math.round(3400 + z * 150 - (x + y) * 25);
          const waterSat = Math.min(0.85, Math.max(0.15, 0.2 + z * 0.15 + (x > 5 ? 0.2 : 0)));
          const netToGross = Math.min(1.0, Math.max(0.4, 0.85 - z * 0.08));

          cells.push({
            x,
            y,
            z,
            porosity: Number(porosity.toFixed(3)),
            permX,
            pressure,
            waterSat: Number(waterSat.toFixed(3)),
            netToGross: Number(netToGross.toFixed(2)),
          });
        }
      }
    }
    return cells;
  }, []);

  const filteredCells = useMemo(() => {
    if (selectedLayerZ === 0) return gridCells; // all layers
    return gridCells.filter((c) => c.z === selectedLayerZ - 1);
  }, [gridCells, selectedLayerZ]);

  const getColor = (cell: Cell3D) => {
    if (property === "porosity") {
      // 0.06 (blue) to 0.32 (red/orange)
      const norm = (cell.porosity - 0.06) / (0.32 - 0.06);
      const hue = (1 - norm) * 240; // 240 (blue) to 0 (red)
      return `hsl(${Math.round(hue)}, 85%, 55%)`;
    }
    if (property === "permX") {
      // 10 to 800 mD
      const logPerm = Math.log10(Math.max(1, cell.permX));
      const norm = Math.min(1, Math.max(0, (logPerm - 1) / 2));
      const hue = 120 + norm * 80;
      return `hsl(${Math.round(hue)}, 90%, 50%)`;
    }
    if (property === "pressure") {
      // 3100 to 4000 psia
      const norm = Math.min(1, Math.max(0, (cell.pressure - 3100) / 900));
      return `hsl(${Math.round(270 - norm * 180)}, 85%, 50%)`;
    }
    if (property === "waterSat") {
      // 0.15 (oil green) to 0.85 (water deep blue)
      const norm = (cell.waterSat - 0.15) / 0.7;
      return `hsl(${Math.round(140 + norm * 80)}, 90%, 45%)`;
    }
    // Net to gross
    const norm = (cell.netToGross - 0.4) / 0.6;
    return `hsl(${Math.round(40 + norm * 80)}, 85%, 50%)`;
  };

  const propertyLabels = {
    porosity: "Porosidade (φ)",
    permX: "Permeabilidade X (mD)",
    pressure: "Pressão (psia)",
    waterSat: "Saturação de Água (Sw)",
    netToGross: "Net-to-Gross (NTG)",
  };

  return (
    <Card className="shadow-md">
      <CardHeader className="flex flex-col md:flex-row md:items-center justify-between pb-4 gap-4">
        <div>
          <CardTitle className="text-xl flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary" />
            Visualização 3D da Malha do Reservatório
          </CardTitle>
          <p className="text-xs text-muted-foreground mt-1">
            Modelo geocelular 3D de alta fidelidade (nx: 8, ny: 8, nz: 4 = 256 blocos) com projeção isométrica interativa.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5 items-center">
          {(["porosity", "permX", "pressure", "waterSat", "netToGross"] as const).map((prop) => (
            <Button
              key={prop}
              size="sm"
              variant={property === prop ? "default" : "outline"}
              onClick={() => setProperty(prop)}
              className="text-xs h-7 px-2.5"
            >
              {prop === "porosity" && "Porosidade"}
              {prop === "permX" && "Perm X"}
              {prop === "pressure" && "Pressão"}
              {prop === "waterSat" && "Sw (Água)"}
              {prop === "netToGross" && "NTG"}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* View Controls & Legend */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-muted/40 p-3 rounded-lg border text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-muted-foreground">Filtro de Camada Z:</span>
            <div className="flex gap-1">
              {[0, 1, 2, 3, 4].map((layer) => (
                <button
                  key={layer}
                  onClick={() => setSelectedLayerZ(layer)}
                  className={`px-2 py-0.5 rounded text-xs transition ${
                    selectedLayerZ === layer
                      ? "bg-primary text-primary-foreground font-semibold"
                      : "bg-background border hover:bg-muted"
                  }`}
                >
                  {layer === 0 ? "Todas (3D)" : `Camada ${layer}`}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-muted-foreground font-medium">Controles:</span>
            <Button size="icon" variant="outline" className="h-6 w-6" onClick={() => setRotationAngle((a) => (a - 15) % 360)}>
              <RotateCcw className="h-3 w-3" />
            </Button>
            <Button size="icon" variant="outline" className="h-6 w-6" onClick={() => setZoom((z) => Math.min(1.4, z + 0.1))}>
              <ZoomIn className="h-3 w-3" />
            </Button>
            <Button size="icon" variant="outline" className="h-6 w-6" onClick={() => setZoom((z) => Math.max(0.7, z - 0.1))}>
              <ZoomOut className="h-3 w-3" />
            </Button>
            <Button size="icon" variant="outline" className="h-6 w-6" onClick={() => { setRotationAngle(30); setTiltAngle(55); setZoom(1); }}>
              <RefreshCw className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* 3D Canvas / Isometric Rendering */}
        <div className="relative w-full h-[380px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center select-none shadow-inner">
          <div
            className="transition-transform duration-300 relative"
            style={{
              transform: `scale(${zoom}) rotateX(${tiltAngle}deg) rotateZ(${rotationAngle}deg)`,
              transformStyle: "preserve-3d",
              width: "280px",
              height: "280px",
            }}
          >
            {/* Axis Grid Plate */}
            <div
              className="absolute inset-0 border border-blue-500/20 bg-blue-950/30 rounded"
              style={{ transform: "translateZ(-10px)" }}
            />

            {/* Voxel Blocks */}
            {filteredCells.map((cell) => {
              const blockSize = 28;
              const gap = 3;
              const posX = cell.x * (blockSize + gap);
              const posY = cell.y * (blockSize + gap);
              const posZ = cell.z * (blockSize + gap) * 1.3;
              const color = getColor(cell);
              const isSelected = selectedCell?.x === cell.x && selectedCell?.y === cell.y && selectedCell?.z === cell.z;

              return (
                <div
                  key={`${cell.x}-${cell.y}-${cell.z}`}
                  onClick={() => setSelectedCell(cell)}
                  className={`absolute rounded cursor-pointer transition-all duration-150 hover:brightness-125 ${
                    isSelected ? "ring-2 ring-white z-50 brightness-125 shadow-lg" : "opacity-90"
                  }`}
                  style={{
                    width: `${blockSize}px`,
                    height: `${blockSize}px`,
                    backgroundColor: color,
                    transform: `translate3d(${posX}px, ${posY}px, ${posZ}px)`,
                    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.3), inset -1px -1px 0 rgba(0,0,0,0.4)",
                  }}
                  title={`Bloco (${cell.x},${cell.y},${cell.z}) - ${propertyLabels[property]}`}
                >
                  {/* Well Indicators on Top Layer */}
                  {cell.z === 0 && cell.x === 1 && cell.y === 1 && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex flex-col items-center">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                      <span className="text-[8px] font-bold text-emerald-300 bg-slate-900 px-1 rounded">P-1</span>
                    </div>
                  )}
                  {cell.z === 0 && cell.x === 6 && cell.y === 6 && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex flex-col items-center">
                      <span className="w-2 h-2 rounded-full bg-blue-400" />
                      <span className="text-[8px] font-bold text-blue-300 bg-slate-900 px-1 rounded">INJ-1</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Floating HUD info */}
          <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md p-2.5 rounded-lg border border-slate-700/60 text-xs text-white max-w-xs space-y-1">
            <div className="font-semibold flex items-center justify-between text-blue-400">
              <span>{propertyLabels[property]}</span>
              <Badge variant="outline" className="text-[10px] py-0 border-blue-400 text-blue-300">
                {filteredCells.length} blocos
              </Badge>
            </div>
            {selectedCell ? (
              <div className="space-y-0.5 pt-1 border-t border-slate-700/80 text-[11px]">
                <p className="font-mono text-emerald-400">
                  Coord: X={selectedCell.x}, Y={selectedCell.y}, Z={selectedCell.z}
                </p>
                <div className="grid grid-cols-2 gap-x-2">
                  <span>Porosidade: {(selectedCell.porosity * 100).toFixed(1)}%</span>
                  <span>Perm X: {selectedCell.permX} mD</span>
                  <span>Pressão: {selectedCell.pressure} psia</span>
                  <span>Sw: {(selectedCell.waterSat * 100).toFixed(1)}%</span>
                  <span>NTG: {(selectedCell.netToGross * 100).toFixed(0)}%</span>
                </div>
              </div>
            ) : (
              <p className="text-slate-400 text-[10px]">Passe o mouse ou clique em um bloco para ver propriedades detalhadas.</p>
            )}
          </div>

          {/* Heatmap color gradient legend */}
          <div className="absolute bottom-3 right-3 bg-slate-900/85 backdrop-blur-md p-2 rounded-lg border border-slate-700/60 text-xs text-white">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] text-slate-400">Baixo</span>
              <div className="w-28 h-2 rounded bg-gradient-to-r from-blue-500 via-green-400 to-red-500" />
              <span className="text-[10px] text-slate-400">Alto</span>
            </div>
            <p className="text-[9px] text-slate-400 text-center">Escala termográfica relativa</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
