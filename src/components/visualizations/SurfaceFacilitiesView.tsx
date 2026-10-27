import React, { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  apparentMolecularWeight,
  gasSpecificGravity,
  gasDensity,
  liquidDensity,
  apiToSG,
  sgToApi,
  wichertAzizCorrection,
  gasCompressibilityFactor,
  beggsRobinsonViscosity,
  oilWaterMixtureViscosity,
  classifyReservoirFluid,
  rvpToTrueVaporPressure,
} from "@/lib/facilities/pvtProperties";
import {
  sizeVerticalTwoPhaseSeparator,
  sizeHorizontalTwoPhaseSeparator,
} from "@/lib/facilities/twoPhaseSeparation";
import {
  sizeVerticalThreePhaseSeparator,
  sizeHorizontalThreePhaseSeparator,
  bucketAndWeirHeightOffset,
} from "@/lib/facilities/threePhaseSeparation";
import {
  calculateMinimumMAWP,
  calculateVesselMechanicalDesign,
  ASME_STEEL_GRADES,
} from "@/lib/facilities/vesselDesign";
import {
  calculateTreatingDropletSize,
  heatRequiredBTUHr,
  gunbarrelWaterLegHeight,
  sizeHorizontalHeaterTreater,
  calculateDesaltingParameters,
} from "@/lib/facilities/oilTreating";
import {
  WORLDWIDE_DISPOSAL_STANDARDS,
  sizeSkimVessels,
  sizeCPIPlatePacks,
  gasFlotationEfficiency,
  sizeDisposalPile,
  filterBetaEfficiency,
  oxygenScavengerRateLbDay,
  calculateWaterScalingIndices,
} from "@/lib/facilities/waterTreating";
import {
  calculateCompressorStages,
  recommendSeparationStages,
  estimateTankBreathingLoss,
  calculateControlValveCv,
} from "@/lib/facilities/processSelection";
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
  ShieldAlert,
  Compass,
  FileText,
  Activity,
  Zap,
  Globe,
  Waves,
} from "lucide-react";

export default function SurfaceFacilitiesView() {
  const [activeTab, setActiveTab] = useState<string>("separation");

  // ==========================================
  // TAB 1: PHASE SEPARATION (CHAPTERS 4 & 5)
  // ==========================================
  const [sepOrientation, setSepOrientation] = useState<"horizontal" | "vertical">("horizontal");
  const [sepPhases, setSepPhases] = useState<"2-phase" | "3-phase">("3-phase");
  const [sepQo, setSepQo] = useState<number>(5000); // BOPD
  const [sepQg, setSepQg] = useState<number>(5.0); // MMscfd
  const [sepQw, setSepQw] = useState<number>(3000); // BWPD
  const [sepP, setSepP] = useState<number>(100); // psia
  const [sepT, setSepT] = useState<number>(90); // °F
  const [sepApi, setSepApi] = useState<number>(30); // °API
  const [sepSgGas, setSepSgGas] = useState<number>(0.6);
  const [sepSgWater, setSepSgWater] = useState<number>(1.07);
  const [sepTro, setSepTro] = useState<number>(10); // min
  const [sepTrw, setSepTrw] = useState<number>(10); // min
  const [sepMuOil, setSepMuOil] = useState<number>(10); // cp

  // Computed 2-Phase Separator
  const twoPhaseVert = useMemo(() => {
    return sizeVerticalTwoPhaseSeparator(sepQg, sepQo, sepP, sepT, 0.99, sepSgGas, sepApi, 140, sepTro);
  }, [sepQg, sepQo, sepP, sepT, sepSgGas, sepApi, sepTro]);

  const twoPhaseHoriz = useMemo(() => {
    return sizeHorizontalTwoPhaseSeparator(sepQg, sepQo, sepP, sepT, 0.99, sepSgGas, sepApi, 140, sepTro);
  }, [sepQg, sepQo, sepP, sepT, sepSgGas, sepApi, sepTro]);

  // Computed 3-Phase Separator
  const threePhaseVert = useMemo(() => {
    return sizeVerticalThreePhaseSeparator(
      sepQg,
      sepQo,
      sepQw,
      sepP,
      sepT,
      0.99,
      sepSgGas,
      sepApi,
      sepSgWater,
      sepMuOil,
      1.0,
      sepTro,
      sepTrw
    );
  }, [sepQg, sepQo, sepQw, sepP, sepT, sepSgGas, sepApi, sepSgWater, sepMuOil, sepTro, sepTrw]);

  const threePhaseHoriz = useMemo(() => {
    return sizeHorizontalThreePhaseSeparator(
      sepQg,
      sepQo,
      sepQw,
      sepP,
      sepT,
      0.99,
      sepSgGas,
      sepApi,
      sepSgWater,
      sepMuOil,
      sepTro,
      sepTrw
    );
  }, [sepQg, sepQo, sepQw, sepP, sepT, sepSgGas, sepApi, sepSgWater, sepMuOil, sepTro, sepTrw]);

  const bucketWeir = useMemo(() => {
    return bucketAndWeirHeightOffset(
      threePhaseHoriz.maxOilPadThicknessInches || 24,
      sepApi,
      sepSgWater
    );
  }, [threePhaseHoriz.maxOilPadThicknessInches, sepApi, sepSgWater]);

  // ==========================================
  // TAB 2: PRESSURE VESSEL DESIGN (CHAPTER 6)
  // ==========================================
  const [pvOpPressure, setPvOpPressure] = useState<number>(125); // psig
  const [pvDiameterInches, setPvDiameterInches] = useState<number>(120); // 10 ft
  const [pvLengthFt, setPvLengthFt] = useState<number>(12); // 12 ft
  const [pvHeadType, setPvHeadType] = useState<"2:1-ellipsoidal" | "cone-bottom">("cone-bottom");
  const [pvApexAngle, setPvApexAngle] = useState<number>(60);
  const [pvMaterial, setPvMaterial] = useState<string>("SA-516-70");
  const [pvJointEff, setPvJointEff] = useState<number>(0.85); // spot radiograph
  const [pvCorrosionAllowance, setPvCorrosionAllowance] = useState<number>(0.25); // in.

  const vesselDesign = useMemo(() => {
    return calculateVesselMechanicalDesign({
      designPressurePsig: pvOpPressure,
      insideDiameterInches: pvDiameterInches,
      seamToSeamLengthFt: pvLengthFt,
      headType: pvHeadType,
      coneApexAngleDeg: pvApexAngle,
      materialKey: pvMaterial,
      jointEfficiency: pvJointEff,
      corrosionAllowanceInches: pvCorrosionAllowance,
      isVertical: true,
      edition: "1998",
    });
  }, [
    pvOpPressure,
    pvDiameterInches,
    pvLengthFt,
    pvHeadType,
    pvApexAngle,
    pvMaterial,
    pvJointEff,
    pvCorrosionAllowance,
  ]);

  const minMawp = useMemo(() => calculateMinimumMAWP(pvOpPressure, true), [pvOpPressure]);

  // ==========================================
  // TAB 3: OIL TREATING & DESALTING (CHAPTER 7)
  // ==========================================
  const [treatQo, setTreatQo] = useState<number>(5000); // BOPD
  const [treatInletTemp, setTreatInletTemp] = useState<number>(80); // °F
  const [treatTargetTemp, setTreatTargetTemp] = useState<number>(100); // °F
  const [treatApi, setTreatApi] = useState<number>(30); // °API
  const [treatWaterCut, setTreatWaterCut] = useState<number>(10); // %
  const [treatOutletWc, setTreatOutletWc] = useState<number>(1.0); // %
  const [treatSalinity, setTreatSalinity] = useState<number>(150000); // ppm

  // Gunbarrel State
  const [gbOilOutletHt, setGbOilOutletHt] = useState<number>(23); // ft
  const [gbInterfaceHt, setGbInterfaceHt] = useState<number>(10); // ft
  const [gbWaterOutletHt, setGbWaterOutletHt] = useState<number>(1); // ft

  const gunbarrel = useMemo(() => {
    return gunbarrelWaterLegHeight(gbOilOutletHt, gbInterfaceHt, gbWaterOutletHt, treatApi, 1.05);
  }, [gbOilOutletHt, gbInterfaceHt, gbWaterOutletHt, treatApi]);

  const treaterSizing = useMemo(() => {
    return sizeHorizontalHeaterTreater(treatQo, treatInletTemp, treatApi, 1.04, 20, [80, 100, 120]);
  }, [treatQo, treatInletTemp, treatApi]);

  const desalting = useMemo(() => {
    return calculateDesaltingParameters(treatQo, treatOutletWc, treatSalinity, 10, 1000);
  }, [treatQo, treatOutletWc, treatSalinity]);

  // ==========================================
  // TAB 4: PRODUCED WATER & INJECTION (CHAPTERS 9 & 10)
  // ==========================================
  const [waterRate, setWaterRate] = useState<number>(5000); // BWPD
  const [waterInletOilPpm, setWaterInletOilPpm] = useState<number>(1000); // mg/L
  const [selectedStandard, setSelectedStandard] = useState<string>("USA-OCS");
  const [deckArea, setDeckArea] = useState<number>(2500); // sq ft
  const [rainfallRate, setRainfallRate] = useState<number>(2.0); // in/hr

  const targetEffluent = WORLDWIDE_DISPOSAL_STANDARDS[selectedStandard]?.limitMgL || 29;

  const waterSkimmer = useMemo(() => {
    return sizeSkimVessels(waterRate, sepApi, 1.07, 1.0, 210, 10);
  }, [waterRate, sepApi]);

  const cpiPacks = useMemo(() => {
    return sizeCPIPlatePacks(waterRate, sepApi, 1.07, 1.0, 60, 45);
  }, [waterRate, sepApi]);

  const flotation = useMemo(() => {
    return gasFlotationEfficiency(0.5, 4);
  }, []);

  const disposalPile = useMemo(() => {
    return sizeDisposalPile(waterRate, deckArea, rainfallRate, 2, sepApi, 5, 10);
  }, [waterRate, deckArea, rainfallRate, sepApi]);

  const scaleIndices = useMemo(() => {
    return calculateWaterScalingIndices(7.8, 200, 160, 400, 140);
  }, []);

  const oxygenScav = useMemo(() => {
    return oxygenScavengerRateLbDay(waterRate, 1.05, 8.0, 2.0, 104);
  }, [waterRate]);

  // ==========================================
  // TAB 5: PVT & PROCESS SELECTION (CHAPTERS 1, 2, 3, 8)
  // ==========================================
  const [pvtP, setPvtP] = useState<number>(1000); // psia
  const [pvtT, setPvtT] = useState<number>(100); // °F
  const [pvtH2S, setPvtH2S] = useState<number>(0.2); // 20%
  const [pvtCO2, setPvtCO2] = useState<number>(0.1); // 10%
  const [pvtRvp, setPvtRvp] = useState<number>(10.0); // psia
  const [compPs, setCompPs] = useState<number>(50); // psia
  const [compPd, setCompPd] = useState<number>(1000); // psia

  const pvtSourGas = useMemo(() => {
    const wa = wichertAzizCorrection(433.9, 826.9, pvtH2S, pvtCO2);
    const pr = pvtP / wa.ppcAdjustedPsia;
    const tr = (pvtT + 459.67) / wa.tpcAdjustedR;
    const z = gasCompressibilityFactor(pr, tr);
    const rho = gasDensity(0.66, pvtP, pvtT + 459.67, z);
    return { wa, pr, tr, z, rho };
  }, [pvtP, pvtT, pvtH2S, pvtCO2]);

  const compressor = useMemo(() => {
    return calculateCompressorStages(compPs, compPd, 10, 3.8);
  }, [compPs, compPd]);

  const stagesRec = useMemo(() => {
    return recommendSeparationStages(compPd - 14.7);
  }, [compPd]);

  const tankLoss = useMemo(() => {
    return estimateTankBreathingLoss(20000);
  }, []);

  const trueVP = useMemo(() => {
    return rvpToTrueVaporPressure(pvtRvp, 100);
  }, [pvtRvp]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Boxes className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight">
              Engenharia de Instalações de Superfície & Processamento
            </h2>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Metodologia Arnold & Stewart (Surface Production Operations, Vol. 1): Separação 2P/3P, Mecânica ASME VIII, Tratamento de Óleo & Gunbarrel, Água Produzida & Injeção, e PVT.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className="text-xs px-3 py-1 bg-primary/10 border-primary/30 text-primary font-semibold">
            Arnold & Stewart (Caps. 1 a 10)
          </Badge>
          <Badge variant="outline" className="text-xs px-3 py-1 bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-semibold">
            Padrão API / ASME
          </Badge>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-muted p-1 grid grid-cols-2 md:grid-cols-5 w-full">
          <TabsTrigger value="separation">1. Separação 2P/3P</TabsTrigger>
          <TabsTrigger value="vessels">2. Mecânica ASME VIII</TabsTrigger>
          <TabsTrigger value="oil-treating">3. Tratador & Gunbarrel</TabsTrigger>
          <TabsTrigger value="water-treating">4. Água & Descarte</TabsTrigger>
          <TabsTrigger value="pvt-process">5. PVT & Processo</TabsTrigger>
        </TabsList>

        {/* ========================================================= */}
        {/* TAB 1: PHASE SEPARATION (CHAPTERS 4 & 5) */}
        {/* ========================================================= */}
        <TabsContent value="separation" className="pt-4 space-y-6">
          {/* Top KPI Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="p-4 bg-primary/5 border-primary/20">
              <p className="text-xs font-medium text-muted-foreground">Vaso Trifásico Recomendado</p>
              <p className="text-2xl font-bold text-primary mt-1 font-mono">
                {threePhaseHoriz.selectedSize.diameterInches}" × {threePhaseHoriz.selectedSize.lengthFt}'
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                SR = {threePhaseHoriz.selectedSize.slendernessRatio} : 1 (API 12J)
              </p>
            </Card>

            <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
              <p className="text-xs font-medium text-muted-foreground">Teto de Diâmetro (d_max)</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {threePhaseHoriz.maxDiameterInches}" <span className="text-xs font-normal">pol</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                (ho)max = {threePhaseHoriz.maxOilPadThicknessInches}" (Eq. 5-6a)
              </p>
            </Card>

            <Card className="p-4 bg-amber-500/5 border-amber-500/20">
              <p className="text-xs font-medium text-muted-foreground">Offset Calha Óleo/Água</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                Δh = {bucketWeir.deltaHInches}" <span className="text-xs font-normal">pol</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Bucket & Weir (Eq. 5-1)</p>
            </Card>

            <Card className="p-4 bg-blue-500/5 border-blue-500/20">
              <p className="text-xs font-medium text-muted-foreground">Vaso Vertical de 3 Fases</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
                {threePhaseVert.dSelectedInches}" × {threePhaseVert.seamToSeamLengthFt}'
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                d_min = {threePhaseVert.dMinInches}" (Ex. 5-1: 90"×20')
              </p>
            </Card>
          </div>

          {/* Form and Sizing Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Filter className="w-4 h-4 text-primary" />
                  Parâmetros de Vazão & Separação
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="sep-qo">Vazão Óleo (BOPD)</Label>
                    <Input id="sep-qo" type="number" value={sepQo} onChange={(e) => setSepQo(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="sep-qg">Vazão Gás (MMscfd)</Label>
                    <Input id="sep-qg" type="number" step="0.5" value={sepQg} onChange={(e) => setSepQg(Number(e.target.value))} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="sep-qw">Água Produzida (BWPD)</Label>
                    <Input id="sep-qw" type="number" value={sepQw} onChange={(e) => setSepQw(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="sep-p">Pressão Vaso (psia)</Label>
                    <Input id="sep-p" type="number" value={sepP} onChange={(e) => setSepP(Number(e.target.value))} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="sep-t">Temperatura (°F)</Label>
                    <Input id="sep-t" type="number" value={sepT} onChange={(e) => setSepT(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="sep-api">Grau API do Óleo</Label>
                    <Input id="sep-api" type="number" value={sepApi} onChange={(e) => setSepApi(Number(e.target.value))} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="sep-tro">Retenção Óleo (min)</Label>
                    <Input id="sep-tro" type="number" value={sepTro} onChange={(e) => setSepTro(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="sep-trw">Retenção Água (min)</Label>
                    <Input id="sep-trw" type="number" value={sepTrw} onChange={(e) => setSepTrw(Number(e.target.value))} />
                  </div>
                </div>

                <div className="p-3 bg-muted/40 rounded space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Arraste CD (gotas 100 μm):</span>
                    <span className="font-bold">{twoPhaseVert.dragCoefficient}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Velocidade Terminal Vt:</span>
                    <span className="font-bold">{twoPhaseVert.terminalVelocityFtS} ft/s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Razão Áreas Aw / A:</span>
                    <span className="font-bold text-primary">{threePhaseHoriz.areaRatioWaterToTotal}</span>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => {
                    setSepQo(5000);
                    setSepQg(5.0);
                    setSepQw(3000);
                    setSepP(100);
                    setSepT(90);
                    setSepApi(30);
                    setSepTro(10);
                    setSepTrw(10);
                    setSepMuOil(10);
                  }}
                >
                  <RefreshCw className="w-3.5 h-3.5 mr-2" />
                  Restaurar Padrão Exemplo 5-1 / 5-3
                </Button>
              </CardContent>
            </Card>

            {/* Separator Engineering Sizing Table */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="shadow-sm">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <Layers className="w-4 h-4 text-primary" />
                      Dimensionamento de Separador Horizontal Trifásico (Half-Full)
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                      Teto d &le; {threePhaseHoriz.maxDiameterInches}"
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Soluções admissíveis que satisfazem simultaneamente a restrição de gás (Eq. 5-3a), retenção de líquido (Eq. 5-4a) e colchão de óleo (Eq. 5-8).
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-md overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-muted text-muted-foreground uppercase text-[10px]">
                        <tr>
                          <th className="p-2.5">Diâmetro (d)</th>
                          <th className="p-2.5">Leff Gás (ft)</th>
                          <th className="p-2.5">Leff Líquido (ft)</th>
                          <th className="p-2.5">Comprimento S/S</th>
                          <th className="p-2.5">Razão L/D</th>
                          <th className="p-2.5">Status API 12J</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y font-mono">
                        {threePhaseHoriz.table.map((row) => (
                          <tr
                            key={row.diameterInches}
                            className={row.isRecommended ? "bg-primary/5 font-semibold text-primary" : "hover:bg-muted/30"}
                          >
                            <td className="p-2.5">{row.diameterInches}" ({(row.diameterInches * 0.0254).toFixed(2)} m)</td>
                            <td className="p-2.5">{row.leffGasFt} ft</td>
                            <td className="p-2.5 text-blue-600 dark:text-blue-400">{row.leffLiquidFt} ft</td>
                            <td className="p-2.5 font-bold">{row.seamToSeamLengthFt} ft</td>
                            <td className="p-2.5">{row.slendernessRatio} : 1</td>
                            <td className="p-2.5 font-sans">
                              {row.isRecommended ? (
                                <Badge className="bg-emerald-600 text-[10px]">Recomendado</Badge>
                              ) : !row.isBelowMaxDiameter ? (
                                <span className="text-rose-500">Excede d_max</span>
                              ) : (
                                <span className="text-muted-foreground">L/D fora de faixa</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t mt-3 text-xs">
                    <div>
                      <span className="text-muted-foreground block text-[11px]">Demanda d*Leff (Gás):</span>
                      <span className="font-mono font-bold text-foreground">{threePhaseHoriz.dLeffGasRequirement}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[11px]">Demanda d²*Leff (Líquido):</span>
                      <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                        {threePhaseHoriz.d2LeffLiquidRequirement.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[11px]">Vaso Selecionado:</span>
                      <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        {threePhaseHoriz.selectedSize.diameterInches}" × {threePhaseHoriz.selectedSize.lengthFt}' S/S
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Bucket & Weir Schematic Card */}
              <Card className="p-4 bg-muted/20 border shadow-sm">
                <h4 className="font-semibold text-xs mb-2 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-amber-500" />
                  Mecanismo Bucket & Weir (Derivação Eq. 5-1)
                </h4>
                <p className="text-xs text-muted-foreground">
                  Para evitar o arraste de óleo pelo fundo da calha de água e garantir a espessura do colchão de óleo ($h_o$), a calha de descarte de água deve ser rebaixada em relação à calha de vertimento de óleo por:
                </p>
                <div className="p-2.5 bg-background border rounded font-mono text-xs mt-2 flex flex-col sm:flex-row justify-between gap-2">
                  <span>Δh = h_o · [1 - (ρ_o / ρ_w)] = <strong>{bucketWeir.deltaHInches}"</strong></span>
                  <span>ρ_óleo = {bucketWeir.rhoOilLbCuFt} lb/ft³</span>
                  <span>ρ_água = {bucketWeir.rhoWaterLbCuFt} lb/ft³</span>
                </div>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 2: PRESSURE VESSEL MECHANICAL DESIGN (CHAPTER 6) */}
        {/* ========================================================= */}
        <TabsContent value="vessels" className="pt-4 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="p-4 bg-primary/5 border-primary/20">
              <p className="text-xs font-medium text-muted-foreground">MAWP Mínimo (com PSH)</p>
              <p className="text-2xl font-bold text-primary mt-1 font-mono">
                {minMawp} <span className="text-xs font-normal">psig</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Cushion seguro s/ alarme</p>
            </Card>

            <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
              <p className="text-xs font-medium text-muted-foreground">Chapa Casco (t_shell)</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {vesselDesign.shellThicknessPlateInches}" <span className="text-xs font-normal">(calc: {vesselDesign.shellThicknessCalcInches}")</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Inclui CA = {pvCorrosionAllowance}"</p>
            </Card>

            <Card className="p-4 bg-amber-500/5 border-amber-500/20">
              <p className="text-xs font-medium text-muted-foreground">Peso Total Estimado</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                {vesselDesign.weights.totalVesselWeightLb.toLocaleString()} <span className="text-xs font-normal">lb</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Ex. 6-1: 35,089 lb</p>
            </Card>

            <Card className="p-4 bg-purple-500/5 border-purple-500/20">
              <p className="text-xs font-medium text-muted-foreground">Velocidade Máxima Bocal</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
                {vesselDesign.maxInletVelocityFtS} <span className="text-xs font-normal">ft/s</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">API RP 14E (Eq. 6-10a)</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-primary" />
                  Especificação Mecânica ASME Seção VIII
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div>
                  <Label htmlFor="pv-press">Pressão de Projeto (psig)</Label>
                  <Input id="pv-press" type="number" value={pvOpPressure} onChange={(e) => setPvOpPressure(Number(e.target.value))} />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="pv-d">Diâmetro Interno (pol)</Label>
                    <Input id="pv-d" type="number" value={pvDiameterInches} onChange={(e) => setPvDiameterInches(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="pv-l">Comprimento S/S (pés)</Label>
                    <Input id="pv-l" type="number" value={pvLengthFt} onChange={(e) => setPvLengthFt(Number(e.target.value))} />
                  </div>
                </div>

                <div>
                  <Label>Geometria do Fundo / Tampos</Label>
                  <Select value={pvHeadType} onChange={(e) => setPvHeadType(e.target.value as any)}>
                    <option value="cone-bottom">Fundo Cônico 60° (Remoção de Areia / Ex. 6-1)</option>
                    <option value="2:1-ellipsoidal">Dois Tampos Elipsoidais 2:1 (Padrão)</option>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label>Aço Estrutural (Tabela 6-3)</Label>
                    <Select value={pvMaterial} onChange={(e) => setPvMaterial(e.target.value)}>
                      <option value="SA-516-70">SA-516 Gr 70 (S=17,500 psi)</option>
                      <option value="SA-516-60">SA-516 Gr 60 (S=15,000 psi)</option>
                      <option value="SA-285-C">SA-285 Gr C (S=13,700 psi)</option>
                      <option value="SA-36">SA-36 (S=16,600 psi)</option>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="pv-ca">Sobrespessura de Corrosão</Label>
                    <Input id="pv-ca" type="number" step="0.0625" value={pvCorrosionAllowance} onChange={(e) => setPvCorrosionAllowance(Number(e.target.value))} />
                  </div>
                </div>

                <div>
                  <Label>Eficiência de Junta E (Tabela 6-4)</Label>
                  <Select value={String(pvJointEff)} onChange={(e) => setPvJointEff(Number(e.target.value))}>
                    <option value="1.0">E = 1.00 (Radiografia Total 100%)</option>
                    <option value="0.85">E = 0.85 (Radiografia por Amostragem Spot)</option>
                    <option value="0.70">E = 0.70 (Sem Inspeção Radiográfica)</option>
                  </Select>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => {
                    setPvOpPressure(125);
                    setPvDiameterInches(120);
                    setPvLengthFt(12);
                    setPvHeadType("cone-bottom");
                    setPvApexAngle(60);
                    setPvMaterial("SA-516-70");
                    setPvJointEff(0.85);
                    setPvCorrosionAllowance(0.25);
                  }}
                >
                  <RefreshCw className="w-3.5 h-3.5 mr-2" />
                  Restaurar Padrão Exemplo 6-1
                </Button>
              </CardContent>
            </Card>

            {/* Vessel Mechanical Weight Breakdown */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <Boxes className="w-4 h-4 text-primary" />
                    Balanço de Espessuras e Composição de Peso do Vaso
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Fórmulas ASME Boiler and Pressure Vessel Code Section VIII Division 1 (Eqs. 6-1 a 6-7).
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 bg-muted/40 rounded border">
                      <span className="text-muted-foreground block text-[11px]">Chapa do Casco:</span>
                      <span className="font-bold font-mono text-foreground text-sm">{vesselDesign.shellThicknessPlateInches}" pol</span>
                      <span className="text-[10px] text-muted-foreground block mt-0.5">W = {vesselDesign.weights.shellWeightLb.toLocaleString()} lb</span>
                    </div>
                    <div className="p-3 bg-muted/40 rounded border">
                      <span className="text-muted-foreground block text-[11px]">Tampo Elipsoidal 2:1:</span>
                      <span className="font-bold font-mono text-foreground text-sm">{vesselDesign.headThicknessPlateInches}" pol</span>
                      <span className="text-[10px] text-muted-foreground block mt-0.5">W = {vesselDesign.weights.headsWeightLb.toLocaleString()} lb</span>
                    </div>
                    {vesselDesign.coneThicknessPlateInches && (
                      <div className="p-3 bg-muted/40 rounded border">
                        <span className="text-muted-foreground block text-[11px]">Cone 60°:</span>
                        <span className="font-bold font-mono text-foreground text-sm">{vesselDesign.coneThicknessPlateInches}" pol</span>
                        <span className="text-[10px] text-muted-foreground block mt-0.5">W = {vesselDesign.weights.coneWeightLb.toLocaleString()} lb</span>
                      </div>
                    )}
                    <div className="p-3 bg-muted/40 rounded border">
                      <span className="text-muted-foreground block text-[11px]">Saia de Suporte:</span>
                      <span className="font-bold font-mono text-foreground text-sm">{vesselDesign.skirtLengthFt} ft alt.</span>
                      <span className="text-[10px] text-muted-foreground block mt-0.5">W = {vesselDesign.weights.skirtWeightLb.toLocaleString()} lb</span>
                    </div>
                  </div>

                  <div className="border rounded-md overflow-hidden">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-muted text-muted-foreground uppercase text-[10px]">
                        <tr>
                          <th className="p-2.5">Componente do Vaso</th>
                          <th className="p-2.5">Equação ASME</th>
                          <th className="p-2.5">Espessura Mínima</th>
                          <th className="p-2.5">Chapa Comercial</th>
                          <th className="p-2.5">Peso Calculado</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y font-mono">
                        <tr>
                          <td className="p-2.5 font-sans font-semibold">Casco Cilíndrico</td>
                          <td className="p-2.5 text-muted-foreground font-sans">Eq. 6-1: Pr / (SE - 0.6P)</td>
                          <td className="p-2.5">{vesselDesign.shellThicknessCalcInches}"</td>
                          <td className="p-2.5 font-bold text-primary">{vesselDesign.shellThicknessPlateInches}"</td>
                          <td className="p-2.5">{vesselDesign.weights.shellWeightLb.toLocaleString()} lb</td>
                        </tr>
                        <tr>
                          <td className="p-2.5 font-sans font-semibold">Tampo Superior 2:1</td>
                          <td className="p-2.5 text-muted-foreground font-sans">Eq. 6-2: Pd / (2SE - 0.2P)</td>
                          <td className="p-2.5">{vesselDesign.headThicknessCalcInches}"</td>
                          <td className="p-2.5 font-bold text-primary">{vesselDesign.headThicknessPlateInches}"</td>
                          <td className="p-2.5">{vesselDesign.weights.headsWeightLb.toLocaleString()} lb</td>
                        </tr>
                        {vesselDesign.coneThicknessCalcInches && (
                          <tr>
                            <td className="p-2.5 font-sans font-semibold">Fundo Cônico 60°</td>
                            <td className="p-2.5 text-muted-foreground font-sans">Eq. 6-4: Pd / (2 cos α(SE - 0.6P))</td>
                            <td className="p-2.5">{vesselDesign.coneThicknessCalcInches}"</td>
                            <td className="p-2.5 font-bold text-primary">{vesselDesign.coneThicknessPlateInches}"</td>
                            <td className="p-2.5">{vesselDesign.weights.coneWeightLb.toLocaleString()} lb</td>
                          </tr>
                        )}
                        <tr>
                          <td className="p-2.5 font-sans font-semibold">Saia & Acessórios</td>
                          <td className="p-2.5 text-muted-foreground font-sans">Eq. 6-8/9 + Internos 10%</td>
                          <td className="p-2.5">—</td>
                          <td className="p-2.5">0.50"</td>
                          <td className="p-2.5">{(vesselDesign.weights.skirtWeightLb + vesselDesign.weights.internalsAndNozzlesLb).toLocaleString()} lb</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 3: CRUDE OIL TREATING, GUNBARREL & DESALTING (CH. 7) */}
        {/* ========================================================= */}
        <TabsContent value="oil-treating" className="pt-4 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="p-4 bg-primary/5 border-primary/20">
              <p className="text-xs font-medium text-muted-foreground">Demanda Térmica (q)</p>
              <p className="text-2xl font-bold text-primary mt-1 font-mono">
                {(treaterSizing.resultsByTemp[1].heatRequiredBtuHr / 1e6).toFixed(2)} <span className="text-xs font-normal">MMBtu/h</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Tratamento a 100°F (Eq. 7-5a)</p>
            </Card>

            <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
              <p className="text-xs font-medium text-muted-foreground">Water Leg Gunbarrel (H)</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {gunbarrel.waterLegHeightHFt} <span className="text-xs font-normal">pés</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Ex. 7-1: 19.5 ft exato</p>
            </Card>

            <Card className="p-4 bg-amber-500/5 border-amber-500/20">
              <p className="text-xs font-medium text-muted-foreground">Gota d_m a 1% BS&W</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                {treaterSizing.resultsByTemp[1].dmMicrons} <span className="text-xs font-normal">μm</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Eq. 7-16 (viscosidade 15 cp)</p>
            </Card>

            <Card className="p-4 bg-purple-500/5 border-purple-500/20">
              <p className="text-xs font-medium text-muted-foreground">Sal residual no Petróleo</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
                {desalting.currentPTB} <span className="text-xs font-normal">PTB</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                {desalting.isDesaltingRequired ? "Requer Dessalinizador (<10 PTB)" : "Em conformidade"}
              </p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Heater-Treater Sizing Section */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Flame className="w-4 h-4 text-orange-500" />
                  Dimensionamento de Tratador Térmico Horizontal (Exemplo 7-2)
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Análise comparativa de sedimentação e aporte térmico para temperaturas de 80°F, 100°F e 120°F.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border rounded-md overflow-hidden text-xs">
                  <table className="w-full text-left">
                    <thead className="bg-muted text-muted-foreground uppercase text-[10px]">
                      <tr>
                        <th className="p-2.5">Temperatura</th>
                        <th className="p-2.5">Viscosidade</th>
                        <th className="p-2.5">Gota dm</th>
                        <th className="p-2.5">d*Leff Req.</th>
                        <th className="p-2.5">Calor (MMBtu/h)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y font-mono">
                      {treaterSizing.resultsByTemp.map((row) => (
                        <tr key={row.tempF} className="hover:bg-muted/30">
                          <td className="p-2.5 font-bold">{row.tempF} °F</td>
                          <td className="p-2.5">{row.muOilCp} cp</td>
                          <td className="p-2.5">{row.dmMicrons} μm</td>
                          <td className="p-2.5 text-blue-600 dark:text-blue-400 font-bold">{row.dLeffRequired}</td>
                          <td className="p-2.5 text-orange-600 dark:text-orange-400 font-bold">
                            {(row.heatRequiredBtuHr / 1e6).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="p-3 bg-muted/40 rounded text-xs space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Restrição de Retenção (d²*Leff):</span>
                    <span className="font-bold">{treaterSizing.d2LeffRetentionRequirement.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tratador Comercial Selecionado:</span>
                    <span className="font-bold text-primary">
                      {treaterSizing.recommendedSize.diameterInches}" × {treaterSizing.recommendedSize.coalescingLengthFt}' (0.86 MMBtu/h)
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Gunbarrel & Desalter Details */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Droplets className="w-4 h-4 text-primary" />
                  Balanço Hidrostático do Gunbarrel & Dessalinizador
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Cálculo do sifão externo (Water Leg) e diluição de salmoura (Exemplo 7-1).
                </p>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="p-3 bg-primary/5 rounded border space-y-2">
                  <h5 className="font-semibold text-foreground flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-primary" />
                    Tanque Gunbarrel com Gas Boot Interno
                  </h5>
                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                    <div>Altura Saída Óleo: <strong>{gbOilOutletHt} ft</strong></div>
                    <div>Altura Interface: <strong>{gbInterfaceHt} ft</strong></div>
                    <div>Gradiente Óleo: <strong>{gunbarrel.oilGradientPsiFt} psi/ft</strong></div>
                    <div>Gradiente Água: <strong>{gunbarrel.waterGradientPsiFt} psi/ft</strong></div>
                  </div>
                  <div className="pt-2 border-t text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    Altura do Water Leg H = ({gunbarrel.oilHeightHoFt}×{gunbarrel.oilGradientPsiFt} + {gunbarrel.waterHeightHwFt}×{gunbarrel.waterGradientPsiFt}) / {gunbarrel.waterGradientPsiFt} = {gunbarrel.waterLegHeightHFt} ft
                  </div>
                </div>

                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded space-y-2">
                  <h5 className="font-semibold text-foreground flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-amber-500" />
                    Dessalinizador Eletrostático de 1 ou 2 Estágios
                  </h5>
                  <div className="space-y-1 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Sal na salmoura ({treatSalinity.toLocaleString()} ppm):</span>
                      <span className="font-bold">{desalting.saltPerBblWaterLb} lb/bbl água</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Teor de Sal no Óleo:</span>
                      <span className="font-bold text-amber-700 dark:text-amber-300">{desalting.currentPTB} PTB</span>
                    </div>
                    {desalting.isDesaltingRequired && (
                      <div className="flex justify-between pt-1 border-t text-primary font-bold">
                        <span>Água de Lavagem Requerida:</span>
                        <span>{desalting.requiredDilutionWaterBpd.toLocaleString()} BPD ({desalting.dilutionRatioPercent}%)</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 4: PRODUCED WATER & INJECTION (CHAPTERS 9 & 10) */}
        {/* ========================================================= */}
        <TabsContent value="water-treating" className="pt-4 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="p-4 bg-primary/5 border-primary/20">
              <p className="text-xs font-medium text-muted-foreground">Norma Regulamentar ({selectedStandard})</p>
              <p className="text-2xl font-bold text-primary mt-1 font-mono">
                {targetEffluent} <span className="text-xs font-normal">mg/L</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Limite máx. de descarte</p>
            </Card>

            <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
              <p className="text-xs font-medium text-muted-foreground">Skimmer Vertical (Ex. 9-2)</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {waterSkimmer.vertical.diameterInches}" × {waterSkimmer.vertical.seamToSeamHeightFt}'
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Coluna d'água: {waterSkimmer.vertical.waterHeightFt} ft</p>
            </Card>

            <Card className="p-4 bg-amber-500/5 border-amber-500/20">
              <p className="text-xs font-medium text-muted-foreground">Pacotes de Placas CPI</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                {cpiPacks.recommendedPacks} <span className="text-xs font-normal">packs</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Corte: dm &ge; {cpiPacks.removableCutoffMicrons} μm</p>
            </Card>

            <Card className="p-4 bg-blue-500/5 border-blue-500/20">
              <p className="text-xs font-medium text-muted-foreground">Disposal Pile Offshore</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
                {disposalPile.standardPipeSizeInches}" <span className="text-xs font-normal">ID</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Submersão: {disposalPile.submergedLengthFt} ft</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Globe className="w-4 h-4 text-primary" />
                  Padrões Globais & Critérios de Descarte
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3.5 text-xs">
                <div>
                  <Label>Jurisdição Ambiental</Label>
                  <Select value={selectedStandard} onChange={(e) => setSelectedStandard(e.target.value)}>
                    {Object.entries(WORLDWIDE_DISPOSAL_STANDARDS).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v.country} ({v.limitMgL} mg/L)
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="p-2.5 bg-muted/40 rounded text-[11px] text-muted-foreground">
                  {WORLDWIDE_DISPOSAL_STANDARDS[selectedStandard]?.notes}
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="wt-rate">Vazão Água (BWPD)</Label>
                    <Input id="wt-rate" type="number" value={waterRate} onChange={(e) => setWaterRate(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="wt-oil">Óleo Entrada (mg/L)</Label>
                    <Input id="wt-oil" type="number" value={waterInletOilPpm} onChange={(e) => setWaterInletOilPpm(Number(e.target.value))} />
                  </div>
                </div>

                <div className="p-3 bg-primary/5 rounded border space-y-1 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span>Remoção Flotação IGF (4 céls):</span>
                    <span className="font-bold text-primary">{flotation.overallEfficiencyPercent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Efluente Pós-Flotação:</span>
                    <span className="font-bold">{(waterInletOilPpm * (1 - flotation.overallEfficiencyPercent / 100)).toFixed(1)} mg/L</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Produced Water Equipment Comparison */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <Waves className="w-4 h-4 text-primary" />
                    Cadeia de Tratamento de Água (Arnold & Stewart Cap. 9)
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Sequência técnica recomendada para conformidade com padrões de descarte offshore e proteção de injeção.
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div className="p-3 bg-muted/30 border rounded">
                      <span className="font-semibold text-primary block mb-1">1. Vaso Skimmer Primário</span>
                      <p className="text-muted-foreground">Remove gotas &ge; 100-210 μm por gravidade contínua.</p>
                      <p className="font-mono font-bold mt-1.5">{waterSkimmer.vertical.diameterInches}" × {waterSkimmer.vertical.seamToSeamHeightFt}' S/S</p>
                    </div>

                    <div className="p-3 bg-muted/30 border rounded">
                      <span className="font-semibold text-primary block mb-1">2. Coalescedor CPI / Placas</span>
                      <p className="text-muted-foreground">Placas corrugadas a 45° removem até 30-60 μm.</p>
                      <p className="font-mono font-bold mt-1.5">{cpiPacks.recommendedPacks} Packs Padronizados</p>
                    </div>

                    <div className="p-3 bg-muted/30 border rounded">
                      <span className="font-semibold text-primary block mb-1">3. Célula Flotação IGF</span>
                      <p className="text-muted-foreground">Microbolhas removem emulsões finas (10-20 μm).</p>
                      <p className="font-mono font-bold mt-1.5">{flotation.overallEfficiencyPercent}% Eficiência Geral</p>
                    </div>
                  </div>

                  {/* Water Injection Indices */}
                  <div className="p-4 bg-background border rounded-lg space-y-2">
                    <h5 className="font-semibold text-xs flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-emerald-500" />
                      Índices de Compatibilidade & Tratamento para Injeção (Cap. 10)
                    </h5>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                      <div>LSI Saturation: <strong>{scaleIndices.langelierIndexLSI}</strong></div>
                      <div>RSI Ryznar: <strong>{scaleIndices.ryznarIndexRSI}</strong></div>
                      <div>Status: <Badge variant="outline" className="text-[10px]">{scaleIndices.scalingTendency}</Badge></div>
                      <div>Sequestrante O2: <strong>{oxygenScav.scavengerRateLbDay} lb/dia</strong></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 5: PVT, COMPRESSION & STABILIZATION (CHAPTERS 1, 2, 3, 8) */}
        {/* ========================================================= */}
        <TabsContent value="pvt-process" className="pt-4 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="p-4 bg-primary/5 border-primary/20">
              <p className="text-xs font-medium text-muted-foreground">Fator Z (Sour Gas)</p>
              <p className="text-2xl font-bold text-primary mt-1 font-mono">
                {pvtSourGas.z}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Wichert-Aziz: ε = {pvtSourGas.wa.epsilon}°R</p>
            </Card>

            <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
              <p className="text-xs font-medium text-muted-foreground">Razão por Estágio (R)</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {compressor.stageRatio} : 1
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">{compressor.numberOfStages} estágios compressor</p>
            </Card>

            <Card className="p-4 bg-amber-500/5 border-amber-500/20">
              <p className="text-xs font-medium text-muted-foreground">True Vapor Pressure (TVP)</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                {trueVP} <span className="text-xs font-normal">psia</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">RVP = {pvtRvp} psia (Fig. 3-49/8-10)</p>
            </Card>

            <Card className="p-4 bg-purple-500/5 border-purple-500/20">
              <p className="text-xs font-medium text-muted-foreground">Economia Válvula de Respiro</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
                {tankLoss.barrelsSavedBblYr} <span className="text-xs font-normal">bbl/ano</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Tanque 20.000 bbl (Tabela 2-3)</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Gauge className="w-4 h-4 text-primary" />
                  Termodinâmica de Gás Ácido (Wichert-Aziz - Ex. 3-6)
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Correção de pseudocríticos na presença de H2S e CO2 (Eqs. 3-22 e 3-23).
                </p>
              </CardHeader>
              <CardContent className="space-y-3.5 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="pvt-p">Pressão (psia)</Label>
                    <Input id="pvt-p" type="number" value={pvtP} onChange={(e) => setPvtP(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="pvt-t">Temperatura (°F)</Label>
                    <Input id="pvt-t" type="number" value={pvtT} onChange={(e) => setPvtT(Number(e.target.value))} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="pvt-h2s">Fração Molar H2S (0-1)</Label>
                    <Input id="pvt-h2s" type="number" step="0.05" value={pvtH2S} onChange={(e) => setPvtH2S(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="pvt-co2">Fração Molar CO2 (0-1)</Label>
                    <Input id="pvt-co2" type="number" step="0.05" value={pvtCO2} onChange={(e) => setPvtCO2(Number(e.target.value))} />
                  </div>
                </div>

                <div className="p-3 bg-muted/40 rounded space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fator de Correção ε:</span>
                    <span className="font-bold">{pvtSourGas.wa.epsilon} °R</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">T''pc Ajustado:</span>
                    <span className="font-bold">{pvtSourGas.wa.tpcAdjustedR} °R</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">P''pc Ajustado:</span>
                    <span className="font-bold">{pvtSourGas.wa.ppcAdjustedPsia} psia</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fator Z Calculado:</span>
                    <span className="font-bold text-primary">{pvtSourGas.z}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Densidade do Gás (ρ_g):</span>
                    <span className="font-bold">{pvtSourGas.rho} lb/ft³</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Wind className="w-4 h-4 text-primary" />
                  Dimensionamento do Trem de Compressão (Eq. 2-2)
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Otimização de estágios com razão constante e pressões intermediárias para o compressor.
                </p>
              </CardHeader>
              <CardContent className="space-y-3.5 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="c-ps">Pressão Sucção Ps (psia)</Label>
                    <Input id="c-ps" type="number" value={compPs} onChange={(e) => setCompPs(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="c-pd">Pressão Descarga Pd (psia)</Label>
                    <Input id="c-pd" type="number" value={compPd} onChange={(e) => setCompPd(Number(e.target.value))} />
                  </div>
                </div>

                <div className="p-3 bg-primary/5 rounded border space-y-2 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span>Número de Estágios:</span>
                    <span className="font-bold text-primary">{compressor.numberOfStages}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Razão por Estágio (R):</span>
                    <span className="font-bold">{compressor.stageRatio}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tipo Recomendado:</span>
                    <span className="font-bold">{compressor.recommendedCompressorType}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Potência Estimada:</span>
                    <span className="font-bold">{compressor.estimatedHp.toLocaleString()} HP</span>
                  </div>
                  <div className="pt-2 border-t text-muted-foreground">
                    Pressões Intermediárias: {compressor.interstagePressuresPsia.join(" psia → ")} psia
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
