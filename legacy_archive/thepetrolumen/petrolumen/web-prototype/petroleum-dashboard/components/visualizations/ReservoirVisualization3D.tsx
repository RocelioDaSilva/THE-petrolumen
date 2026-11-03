"use client";
import React, { Suspense, useRef, useState, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { generateReservoirProperties } from "../../lib/connectors/databases";

const propertyOptions = [
  { key: "porosity", label: "Porosity" },
  { key: "permeability_x", label: "Perm X" },
  { key: "permeability_y", label: "Perm Y" },
  { key: "permeability_z", label: "Perm Z" },
  { key: "pressure", label: "Pressure" },
  { key: "water_saturation", label: "Water Sat" },
  { key: "net_to_gross", label: "Net/Gross" },
];

function getColor(cell: any, property: string) {
  // Simple color mapping for demo
  const value = cell[property];
  if (property.includes("perm")) return `hsl(${120 + value / 10}, 80%, 60%)`;
  if (property === "porosity") return `hsl(${180 + value * 100}, 80%, 60%)`;
  if (property === "pressure") return `hsl(${240 - (value - 3000) / 10}, 80%, 60%)`;
  if (property === "water_saturation") return `#3b82f6`;
  if (property === "net_to_gross") return `#a21caf`;
  return "#ccc";
}

export default function ReservoirVisualization3D() {
  const [property, setProperty] = useState("porosity");
  const [selectedCell, setSelectedCell] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cells, setCells] = useState<any[]>([]);
  const [modules, setModules] = useState<string[]>([]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setTimeout(() => {
      try {
        const data = generateReservoirProperties();
        setCells(data.properties.map((cell: any, i: number) => ({
          ...cell,
          x: Number(cell.block_id.split(",")[0]),
          y: Number(cell.block_id.split(",")[1]),
          z: Number(cell.block_id.split(",")[2]),
          id: cell.block_id,
        })));
        setLoading(false);
      } catch (e) {
        setError("Failed to load reservoir data.");
        setLoading(false);
      }
    }, 800);
  }, []);

  useEffect(() => {
    fetch('http://localhost:8000/status') // Adjust port if needed
      .then(res => res.json())
      .then(data => {
        setModules(data.modules || []);
      });
  }, []);

  if (loading) return <div className="skeleton h-96 w-full rounded-lg" />;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>3D Reservoir Grid Visualization</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-2 flex gap-2">
          {propertyOptions.map((opt) => (
            <Button
              key={opt.key}
              size="sm"
              variant={property === opt.key ? "default" : "outline"}
              onClick={() => setProperty(opt.key)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
        <div className="w-full h-[400px] bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg shadow relative">
          <Canvas camera={{ position: [30, 30, 30], fov: 50 }}>
            <ambientLight />
            <pointLight position={[10, 10, 10]} />
            <OrbitControls />
            <Suspense fallback={null}>
              {cells.map((cell) => (
                <mesh
                  key={cell.id}
                  position={[cell.x, cell.y, cell.z]}
                  onPointerOver={() => setSelectedCell(cell)}
                  onPointerOut={() => setSelectedCell(null)}
                >
                  <boxGeometry args={[0.9, 0.9, 0.9]} />
                  <meshStandardMaterial color={getColor(cell, property)} />
                  {selectedCell?.id === cell.id && (
                    <Html>
                      <div className="bg-white p-2 rounded shadow text-xs">
                        <div>Porosity: {cell.porosity.toFixed(2)}</div>
                        <div>Perm X: {cell.permeability_x.toFixed(1)}</div>
                        <div>Perm Y: {cell.permeability_y.toFixed(1)}</div>
                        <div>Perm Z: {cell.permeability_z.toFixed(1)}</div>
                        <div>Pressure: {cell.pressure.toFixed(1)}</div>
                        <div>Water Sat: {cell.water_saturation.toFixed(2)}</div>
                        <div>Net/Gross: {cell.net_to_gross.toFixed(2)}</div>
                      </div>
                    </Html>
                  )}
                </mesh>
              ))}
            </Suspense>
          </Canvas>
        </div>
        <div className="mt-4">
          <h2 className="text-xl font-semibold mb-2">Available Simulation Modules</h2>
          {loading ? (
            <div>Loading...</div>
          ) : (
            <ul>
              {modules.map((mod) => (
                <li key={mod}>{mod}</li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
} 