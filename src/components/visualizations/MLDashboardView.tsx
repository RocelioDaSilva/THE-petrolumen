import React, { useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Brain, Cpu, Sparkles, CheckCircle, Play, Layers } from "lucide-react";

export default function MLDashboardView() {
  const [selectedModel, setSelectedModel] = useState<"xgboost" | "svr" | "lstm">("xgboost");
  const [targetFeature, setTargetFeature] = useState<string>("oil_rate");
  const [training, setTraining] = useState<boolean>(false);
  const [modelTrained, setModelTrained] = useState<boolean>(true);

  // Training results metrics
  const metrics = {
    xgboost: { r2: 0.962, rmse: 42.5, mae: 31.8, best: "XGBoost Regressor (Optuna Tuned)" },
    svr: { r2: 0.918, rmse: 68.2, mae: 52.4, best: "Support Vector Regressor (RBF Kernel)" },
    lstm: { r2: 0.954, rmse: 48.1, mae: 36.5, best: "LSTM Deep Neural Forecaster (2 Layers)" },
  }[selectedModel];

  // Forecast Comparison Data (Actual vs ML Predicted)
  const forecastComparison = [
    { month: "Mês 1", actual: 1250, pred: 1245 },
    { month: "Mês 2", actual: 1180, pred: 1192 },
    { month: "Mês 3", actual: 1120, pred: 1115 },
    { month: "Mês 4", actual: 1060, pred: 1068 },
    { month: "Mês 5", actual: 1010, pred: 1005 },
    { month: "Mês 6", actual: 970, pred: 965 },
    { month: "Mês 7", actual: 930, pred: 938 },
    { month: "Mês 8", actual: 890, pred: 885 },
    { month: "Mês 9", actual: 860, pred: 865 },
    { month: "Mês 10", actual: 825, pred: 820 },
    { month: "Mês 11", actual: 800, pred: 795 },
    { month: "Mês 12", actual: 775, pred: 778 },
    { month: "Mês 13 (F)", actual: null, pred: 755 },
    { month: "Mês 14 (F)", actual: null, pred: 735 },
    { month: "Mês 15 (F)", actual: null, pred: 715 },
    { month: "Mês 16 (F)", actual: null, pred: 698 },
  ];

  // Feature Importance
  const featureWeights = [
    { feature: "Pressão de Fundo (Pwf)", weight: 38 },
    { feature: "Produção Acumulada (Np)", weight: 26 },
    { feature: "Abertura de Choke (%)", weight: 18 },
    { feature: "Water Cut (BSW)", weight: 12 },
    { feature: "Tempo Decorrido (t)", weight: 6 },
  ];

  const handleTrain = () => {
    setTraining(true);
    setTimeout(() => {
      setTraining(false);
      setModelTrained(true);
    }, 800);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="w-6 h-6 text-primary" />
            Analytics Avançado & Previsão por Machine Learning
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Treinamento e inferência supervisionada com algoritmos XGBoost, SVR e LSTM para predição de vazões e identificação de anomalias.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-primary/10 border-primary/30 text-primary">
            Modelo: {selectedModel.toUpperCase()}
          </Badge>
          <Button onClick={handleTrain} disabled={training} className="shadow">
            <Play className={`w-4 h-4 mr-2 ${training ? "animate-spin" : ""}`} />
            {training ? "Treinando Modelos..." : "Re-treinar Algoritmo"}
          </Button>
        </div>
      </div>

      {/* Model Selection and Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="p-4 bg-primary/5 border-primary/20">
          <p className="text-xs font-medium text-muted-foreground">Melhor Modelo Ativo</p>
          <p className="text-lg font-bold text-primary mt-1">{selectedModel.toUpperCase()}</p>
          <p className="text-[11px] text-muted-foreground mt-1 truncate">{metrics.best}</p>
        </Card>
        <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-xs font-medium text-muted-foreground">Coeficiente de Determinação (R²)</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {metrics.r2.toFixed(3)}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Acurácia estatística global</p>
        </Card>
        <Card className="p-4 bg-blue-500/5 border-blue-500/20">
          <p className="text-xs font-medium text-muted-foreground">Erro Quadrático Médio (RMSE)</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
            {metrics.rmse} STB/d
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Desvio padrão dos resíduos</p>
        </Card>
        <Card className="p-4 bg-purple-500/5 border-purple-500/20">
          <p className="text-xs font-medium text-muted-foreground">Erro Médio Absoluto (MAE)</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
            {metrics.mae} STB/d
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Erro médio de inferência</p>
        </Card>
      </div>

      {/* Main Grid: Controls + Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Architecture & Feature Selector */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Configuração do Treinamento</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Algoritmo de Aprendizado</label>
              <div className="grid grid-cols-3 gap-2">
                {(["xgboost", "svr", "lstm"] as const).map((m) => (
                  <Button
                    key={m}
                    size="sm"
                    variant={selectedModel === m ? "default" : "outline"}
                    className="text-xs uppercase"
                    onClick={() => setSelectedModel(m)}
                  >
                    {m}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Variável Alvo (Target)</label>
              <div className="p-2.5 bg-muted/40 rounded border text-xs font-mono text-primary font-bold">
                oil_rate (Vazão de Óleo - STB/d)
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t">
              <label className="text-xs font-semibold text-muted-foreground uppercase">
                Importância das Features (Pesos SHAP)
              </label>
              <div className="space-y-2">
                {featureWeights.map((fw) => (
                  <div key={fw.feature} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>{fw.feature}</span>
                      <span className="font-mono font-semibold">{fw.weight}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${fw.weight * 2.2}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Prediction Chart */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">
              Previsão de Produção ML vs Histórico Medido
            </CardTitle>
            <Badge variant="outline" className="text-xs">Horizonte de 16 Meses</Badge>
          </CardHeader>
          <CardContent>
            {training ? (
              <div className="space-y-4 py-12">
                <Skeleton className="h-8 w-3/4 mx-auto" />
                <Skeleton className="h-48 w-full" />
              </div>
            ) : (
              <div className="h-[340px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastComparison} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="month" />
                    <YAxis label={{ value: "Vazão (STB/d)", angle: -90, position: "insideLeft", offset: 0 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} />
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="#10b981"
                      strokeWidth={2.5}
                      name="Medição de Campo Real"
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="pred"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      name={`Predição ${selectedModel.toUpperCase()}`}
                      strokeDasharray="4 4"
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
