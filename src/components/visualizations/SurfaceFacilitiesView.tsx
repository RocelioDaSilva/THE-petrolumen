import React, { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import {
  sizeSeparator,
  sizeTEGDehydration,
  SeparatorInput,
  DehydrationInputs,
} from "@/lib/facilitiesMath";
import {
  Boxes,
  Flame,
  Droplets,
  Wind,
  Layers,
  Filter,
  CheckCircle,
  RefreshCw,
  Gauge,
} from "lucide-react";

export default function SurfaceFacilitiesView() {
  // Separator Sizing state
  const [orientation, setOrientation] = useState<"horizontal" | "vertical">("horizontal");
  const [phases, setPhases] = useState<"2-phase" | "3-phase">("3-phase");
  const [oilRateBopd, setOilRateBopd] = useState<number>(4500);
  const [gasRateMmscfd, setGasRateMmscfd] = useState<number>(8.5);
  const [waterRateBwpd, setWaterRateBwpd] = useState<number>(1800);
  const [operatingPressurePsia, setOperatingPressurePsia] = useState<number>(480);
  const [operatingTemperatureF, setOperatingTemperatureF] = useState<number>(110);
  const [oilApi, setOilApi] = useState<number>(33.5);
  const [gasGravity, setGasGravity] = useState<number>(0.72);
  const [retentionTimeMin, setRetentionTimeMin] = useState<number>(4);

  // Glycol Dehydration state
  const [gasDehydrationRate, setGasDehydrationRate] = useState<number>(8.5); // MMscfd
  const [dehydrationPressure, setDehydrationPressure] = useState<number>(950); // psia
  const [dehydrationTemp, setDehydrationTemp] = useState<number>(95); // °F
  const [outletDewPoint, setOutletDewPoint] = useState<number>(20); // °F (pipeline standard)

  const separator = useMemo(() => {
    return sizeSeparator({
      orientation,
      phases,
      oilRateBopd,
      gasRateMmscfd,
      waterRateBwpd,
      operatingPressurePsia,
      operatingTemperatureF,
      oilApi,
      gasGravity,
      waterGravity: 1.05,
      liquidRetentionTimeMin: retentionTimeMin,
      dropletCutoffMicrons: 100,
    });
  }, [
    orientation,
    phases,
    oilRateBopd,
    gasRateMmscfd,
    waterRateBwpd,
    operatingPressurePsia,
    operatingTemperatureF,
    oilApi,
    gasGravity,
    retentionTimeMin,
  ]);

  const dehydration = useMemo(() => {
    return sizeTEGDehydration({
      gasFlowRateMmscfd: gasDehydrationRate,
      operatingPressurePsia: dehydrationPressure,
      inletGasTemperatureF: dehydrationTemp,
      outletDewPointTargetF: outletDewPoint,
      tegCirculationRateGalPerLbWater: 3.0,
    });
  }, [gasDehydrationRate, dehydrationPressure, dehydrationTemp, outletDewPoint]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Boxes className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight">
              Instalações de Superfície & Dimensionamento de Separadores
            </h2>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Metodologia Arnold & Stewart (Surface Production Operations) para vasos bifásicos/trifásicos, desidratação por glicol (TEG) e tratamento de água produzida.
          </p>
        </div>
        <Badge variant="outline" className="text-xs px-3 py-1 bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-semibold">
          Vaso Recomendado: {separator.vesselDiameterInches}" ID × {separator.seamToSeamLengthFt}' S/S (L/D: {separator.slendernessRatio})
        </Badge>
      </div>

      {/* KPI Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 bg-primary/5 border-primary/20">
          <p className="text-xs font-medium text-muted-foreground">Diâmetro Interno do Vaso (ID)</p>
          <p className="text-2xl font-bold text-primary mt-1 font-mono">
            {separator.vesselDiameterInches} <span className="text-xs font-normal">pol ({(separator.vesselDiameterInches * 0.0254).toFixed(2)} m)</span>
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Padronizado em casco industrial</p>
        </Card>

        <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-xs font-medium text-muted-foreground">Comprimento Costura a Costura (S/S)</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {separator.seamToSeamLengthFt} <span className="text-xs font-normal">pés ({(separator.seamToSeamLengthFt * 0.3048).toFixed(1)} m)</span>
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Razão L/D = {separator.slendernessRatio}:1</p>
        </Card>

        <Card className="p-4 bg-blue-500/5 border-blue-500/20">
          <p className="text-xs font-medium text-muted-foreground">Capacidade Máxima de Líquido</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
            {separator.liquidCapacityBpd.toLocaleString()} <span className="text-xs font-normal">BPD</span>
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Tempo retenção: {retentionTimeMin} min</p>
        </Card>

        <Card className="p-4 bg-purple-500/5 border-purple-500/20">
          <p className="text-xs font-medium text-muted-foreground">Coluna de Glicol TEG</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
            {dehydration.contactorDiameterInches} <span className="text-xs font-normal">pol</span>
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Circulação: {dehydration.tegCirculationRateGpm} GPM</p>
        </Card>
      </div>

      {/* Main Grid: Sizing Inputs & Visual Schematic */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Filter className="w-4 h-4 text-primary" />
              Parâmetros de Operação do Separador
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3.5 text-xs">
            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label>Orientação do Vaso</Label>
                <Select
                  value={orientation}
                  onChange={(e) => setOrientation(e.target.value as any)}
                >
                  <option value="horizontal">Horizontal (Padrão)</option>
                  <option value="vertical">Vertical</option>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Separação de Fases</Label>
                <Select
                  value={phases}
                  onChange={(e) => setPhases(e.target.value as any)}
                >
                  <option value="3-phase">Trifásico (Óleo/Gás/Água)</option>
                  <option value="2-phase">Bifásico (Óleo/Gás)</option>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label htmlFor="fac-oil">Vazão de Óleo (BOPD)</Label>
                <Input
                  id="fac-oil"
                  type="number"
                  step="250"
                  value={oilRateBopd}
                  onChange={(e) => setOilRateBopd(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="fac-gas">Vazão de Gás (MMSCFD)</Label>
                <Input
                  id="fac-gas"
                  type="number"
                  step="0.5"
                  value={gasRateMmscfd}
                  onChange={(e) => setGasRateMmscfd(Number(e.target.value))}
                />
              </div>
            </div>

            {phases === "3-phase" && (
              <div className="space-y-1">
                <Label htmlFor="fac-water">Vazão de Água Produzida (BWPD)</Label>
                <Input
                  id="fac-water"
                  type="number"
                  step="200"
                  value={waterRateBwpd}
                  onChange={(e) => setWaterRateBwpd(Number(e.target.value))}
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label htmlFor="fac-p">Pressão de Operação (psia)</Label>
                <Input
                  id="fac-p"
                  type="number"
                  value={operatingPressurePsia}
                  onChange={(e) => setOperatingPressurePsia(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="fac-t">Temperatura (°F)</Label>
                <Input
                  id="fac-t"
                  type="number"
                  value={operatingTemperatureF}
                  onChange={(e) => setOperatingTemperatureF(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label htmlFor="fac-api">Grau API do Óleo</Label>
                <Input
                  id="fac-api"
                  type="number"
                  step="0.5"
                  value={oilApi}
                  onChange={(e) => setOilApi(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="fac-ret">Tempo Retenção Líquido (min)</Label>
                <Input
                  id="fac-ret"
                  type="number"
                  step="0.5"
                  value={retentionTimeMin}
                  onChange={(e) => setRetentionTimeMin(Number(e.target.value))}
                />
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
              onClick={() => {
                setOilRateBopd(4500);
                setGasRateMmscfd(8.5);
                setWaterRateBwpd(1800);
                setOperatingPressurePsia(480);
                setOperatingTemperatureF(110);
                setOilApi(33.5);
                setRetentionTimeMin(4);
              }}
            >
              <RefreshCw className="w-3 h-3 mr-2" />
              Restaurar Parâmetros Base
            </Button>
          </CardContent>
        </Card>

        {/* Separator Cross-Section Schematic & Dehydration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Visual Vessel Diagram */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Layers className="w-4 h-4 text-primary" />
                  Corte Esquemático do Separador Industrial ({orientation.toUpperCase()})
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Representação visual de separação por gravidade e velocidades de sedimentação de gotas.
                </p>
              </div>
              <Badge variant="outline" className="text-xs font-mono">
                {separator.retentionVolumeBbl} bbl volume líquido
              </Badge>
            </CardHeader>
            <CardContent>
              {/* Vessel Graphic */}
              <div className="w-full h-48 bg-slate-900 rounded-xl p-4 border border-slate-800 relative flex flex-col justify-between overflow-hidden shadow-inner">
                {/* Gas Phase top zone */}
                <div className="relative z-10 flex justify-between items-center text-xs text-slate-300 px-3 py-1 bg-slate-800/60 rounded">
                  <span className="flex items-center gap-1.5 font-semibold text-amber-400">
                    <Wind className="w-3.5 h-3.5" />
                    Espaço de Gás & Extrator de Névoa (Mist Pad)
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Vt = {separator.terminalVelocityFtSec} ft/s (Gotas &gt; 100μm)
                  </span>
                </div>

                {/* Liquid Levels */}
                <div className="space-y-1 relative z-10">
                  {/* Oil layer */}
                  <div className="h-10 rounded bg-gradient-to-r from-amber-700/80 to-amber-600/80 border border-amber-500/40 flex items-center justify-between px-3 text-xs text-amber-100 font-medium">
                    <span>Camada de Óleo Contínuo</span>
                    <span className="text-[11px] font-mono">API {oilApi}°</span>
                  </div>

                  {/* Water layer for 3-phase */}
                  {phases === "3-phase" && (
                    <div className="h-8 rounded bg-gradient-to-r from-blue-700/80 to-blue-600/80 border border-blue-500/40 flex items-center justify-between px-3 text-xs text-blue-100 font-medium">
                      <span>Água Produzida Separada</span>
                      <span className="text-[11px] font-mono">Interface: ~{separator.oilWaterInterfaceInches}"</span>
                    </div>
                  )}
                </div>

                {/* Vessel Shell Outline */}
                <div className="absolute inset-0 border-2 border-slate-600/40 rounded-xl pointer-events-none" />
              </div>

              {/* Geometry specs table */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t text-xs">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Diâmetro ID:</span>
                  <span className="font-mono font-bold text-foreground">{separator.vesselDiameterInches} polegadas</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Comprimento S/S:</span>
                  <span className="font-mono font-bold text-foreground">{separator.seamToSeamLengthFt} pés</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Razão de Esbeltez:</span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {separator.slendernessRatio} : 1
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Velocidade Terminal:</span>
                  <span className="font-mono font-bold text-primary">{separator.terminalVelocityFtSec} ft/s</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Glycol Dehydration (TEG Contactor) */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Droplets className="w-4 h-4 text-purple-500" />
                  Desidratação de Gás Natural por Trietilenoglicol (TEG)
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Dimensionamento da coluna de absorção e taxa de circulação para especificação de duto.
                </p>
              </div>
              <Badge variant="outline" className="text-xs bg-purple-500/10 text-purple-600 border-purple-500/30">
                Ponto de Orvalho Alvo: {outletDewPoint}°F
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="text-muted-foreground">Teor de Água na Entrada:</p>
                  <p className="text-lg font-bold font-mono text-foreground">{dehydration.inletWaterContentLbMmscf} lb/MMscf</p>
                  <p className="text-[10px] text-muted-foreground">Saturado a {dehydrationTemp}°F</p>
                </div>

                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="text-muted-foreground">Teor de Água na Saída:</p>
                  <p className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
                    {dehydration.outletWaterContentLbMmscf} lb/MMscf
                  </p>
                  <p className="text-[10px] text-muted-foreground">Espec duto: &lt; 7 lb/MMscf</p>
                </div>

                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="text-muted-foreground">Água Total Removida:</p>
                  <p className="text-lg font-bold font-mono text-primary">{dehydration.waterRemovedLbDay} lb/dia</p>
                  <p className="text-[10px] text-muted-foreground">{gasDehydrationRate} MMscfd tratado</p>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-3 pt-3 border-t text-xs">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Diâmetro Coluna TEG:</span>
                  <span className="font-mono font-bold text-foreground">{dehydration.contactorDiameterInches} polegadas</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Circulação TEG:</span>
                  <span className="font-mono font-bold text-purple-600 dark:text-purple-400">{dehydration.tegCirculationRateGpm} GPM</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Carga Térmica Reboiler:</span>
                  <span className="font-mono font-bold text-foreground">{(dehydration.glycolReboilerDutyBtuHr / 1000).toFixed(0)} MBtu/h</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
