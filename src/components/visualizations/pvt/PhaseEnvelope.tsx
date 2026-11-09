import {
  CartesianGrid,
  Legend,
  ReferenceDot,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface PhaseEnvelopePoint {
  temperature: number;
  pressure: number;
  type: "bubble" | "dew" | "critical" | "critical_estimate";
}

interface PhaseEnvelopeProps {
  points: PhaseEnvelopePoint[];
  temperatureUnit: string;
  pressureUnit: string;
}

export function PhaseEnvelope({
  points,
  temperatureUnit,
  pressureUnit,
}: PhaseEnvelopeProps) {
  const bubblePoints = points
    .filter((point) => point.type === "bubble")
    .sort((left, right) => left.temperature - right.temperature);
  const dewPoints = points
    .filter((point) => point.type === "dew")
    .sort((left, right) => left.temperature - right.temperature);
  const criticalPoint = points.find(
    (point) =>
      point.type === "critical" || point.type === "critical_estimate",
  );
  const envelopePoints = [...bubblePoints, ...dewPoints];
  const cricondentherm =
    envelopePoints.length > 0
      ? Math.max(...envelopePoints.map((point) => point.temperature))
      : undefined;
  const cricondenbar =
    envelopePoints.length > 0
      ? Math.max(...envelopePoints.map((point) => point.pressure))
      : undefined;

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">Phase envelope</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {envelopePoints.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No phase-envelope points are available.
          </p>
        ) : (
          <>
            <div className="h-[240px] w-full" role="img" aria-label="Phase envelope chart">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 12, right: 16, bottom: 20, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis
                    type="number"
                    dataKey="temperature"
                    name="Temperature"
                    unit={` ${temperatureUnit}`}
                    label={{
                      value: `Temperature (${temperatureUnit})`,
                      position: "insideBottom",
                      offset: -12,
                    }}
                  />
                  <YAxis
                    type="number"
                    dataKey="pressure"
                    name="Pressure"
                    unit={` ${pressureUnit}`}
                    label={{
                      value: `Pressure (${pressureUnit})`,
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                  <Legend />
                  {bubblePoints.length > 0 && (
                    <Scatter
                      name="Bubble point"
                      data={bubblePoints}
                      line={{ stroke: "#ef4444", strokeWidth: 2 }}
                      fill="#ef4444"
                    />
                  )}
                  {dewPoints.length > 0 && (
                    <Scatter
                      name="Dew point"
                      data={dewPoints}
                      line={{ stroke: "#10b981", strokeWidth: 2 }}
                      fill="#10b981"
                    />
                  )}
                  {criticalPoint && (
                    <ReferenceDot
                      x={criticalPoint.temperature}
                      y={criticalPoint.pressure}
                      r={6}
                      fill="#f97316"
                      stroke="white"
                      label="Critical point"
                    />
                  )}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
              {criticalPoint && (
                <div>
                  <dt className="text-muted-foreground">Critical point</dt>
                  <dd className="font-medium">
                    {criticalPoint.temperature.toFixed(1)} {temperatureUnit},{" "}
                    {criticalPoint.pressure.toFixed(1)} {pressureUnit}
                  </dd>
                </div>
              )}
              {cricondentherm !== undefined && (
                <div>
                  <dt className="text-muted-foreground">Cricondentherm</dt>
                  <dd className="font-medium">
                    {cricondentherm.toFixed(1)} {temperatureUnit}
                  </dd>
                </div>
              )}
              {cricondenbar !== undefined && (
                <div>
                  <dt className="text-muted-foreground">Cricondenbar</dt>
                  <dd className="font-medium">
                    {cricondenbar.toFixed(1)} {pressureUnit}
                  </dd>
                </div>
              )}
            </dl>
          </>
        )}
      </CardContent>
    </Card>
  );
}
