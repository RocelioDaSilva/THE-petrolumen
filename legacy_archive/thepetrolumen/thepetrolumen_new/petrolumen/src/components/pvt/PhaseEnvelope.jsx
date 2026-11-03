import React, { useState, useEffect, useCallback } from 'react';
import {
  ScatterChart, Scatter, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Label, ReferenceDot
} from 'recharts';
import { fetchPhaseEnvelope } from '../../services/pvtService'; // Adjust path as needed

const PhaseEnvelopeChart = ({ modelName, refreshTrigger }) => { // Added refreshTrigger
  const [envelopeData, setEnvelopeData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [temperatureRange, setTemperatureRange] = useState({ start: 0, end: 350, step: 10 }); // °F
  const [maxPressure, setMaxPressure] = useState(10000); // psia

  const fetchData = useCallback(async () => {
    if (!modelName) {
      setEnvelopeData([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchPhaseEnvelope({
        model_name: modelName,
        temperature_range: [temperatureRange.start, temperatureRange.end, temperatureRange.step],
        max_pressure: maxPressure
      });

      if (!data || data.length === 0) {
        setError('No data returned for phase envelope. Ensure model is compositional and parameters are valid.');
        setEnvelopeData([]);
      } else {
        setEnvelopeData(data);
      }
    } catch (err) {
      console.error('Failed to generate phase envelope:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to generate phase envelope.');
      setEnvelopeData([]);
    } finally {
      setIsLoading(false);
    }
  }, [modelName, temperatureRange, maxPressure]); // Dependencies for useCallback

  useEffect(() => {
    fetchData();
  }, [fetchData, refreshTrigger]); // Effect runs when fetchData (due to its own deps) or refreshTrigger changes

  const criticalPoint = envelopeData.find(point => point.type === 'critical' || point.type === 'critical_estimate');
  const bubblePoints = envelopeData.filter(p => p.type === 'bubble').sort((a,b) => a.temperature - b.temperature);
  const dewPoints = envelopeData.filter(p => p.type === 'dew').sort((a,b) => a.temperature - b.temperature);

  // Calculate Cricondentherm and Cricondenbar
  const cricondentherm = dewPoints.length > 0 ? Math.max(...dewPoints.map(p => p.temperature)) : null;
  const cricondenbar = bubblePoints.length > 0 ? Math.max(...bubblePoints.map(p => p.pressure), ...(dewPoints.map(p=>p.pressure))) : null;


  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center h-96 bg-gray-50 rounded-lg">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <p className="mt-3 text-gray-600">Generating Phase Envelope...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-700 shadow-sm">
        <h4 className="font-semibold mb-1">Error Generating Phase Envelope:</h4>
        <p className="text-sm">{error}</p>
        <button onClick={fetchData} className="mt-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200">
            Retry
        </button>
      </div>
    );
  }

  if (envelopeData.length === 0 && !isLoading) { // Check after loading attempt
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center text-gray-500 shadow-sm">
        <p>No phase envelope data available for "{modelName}".</p>
        <p className="text-xs mt-1">Ensure it's a compositional model with valid components and try generating.</p>
         <button onClick={fetchData} className="mt-2 text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200">
            Refresh/Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="font-semibold text-lg mb-1 text-gray-700">Phase Envelope: {modelName}</h3>
      <p className="text-xs text-gray-500 mb-4">Diagram shows the phase behavior of the fluid mixture at different pressures and temperatures.</p>

      {/* Controls for T-range and P-max could be added here if desired */}

      <div className="h-96 md:h-[500px] w-full"> {/* Responsive height */}
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0"/>
            <XAxis
              type="number"
              dataKey="temperature"
              name="Temperature"
              unit="°F"
              label={{ value: 'Temperature (°F)', position: 'insideBottom', offset: -15, dy:10 }}
              domain={['dataMin - 10', 'dataMax + 10']}
              tickFormatter={(val) => parseFloat(val).toFixed(0)}
            />
            <YAxis
              type="number"
              dataKey="pressure"
              name="Pressure"
              unit=" psia"
              label={{ value: 'Pressure (psia)', angle: -90, position: 'insideLeft', dx: -10 }}
              domain={[0, 'dataMax + 500']}
              tickFormatter={(val) => parseFloat(val).toFixed(0)}
            />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name, props) => [`${parseFloat(value).toFixed(2)} ${props.unit || ''}`, name]}
            />
            <Legend verticalAlign="top" height={36}/>

            {bubblePoints.length > 0 && (
              <Line
                type="monotone"
                data={bubblePoints}
                dataKey="pressure"
                name="Bubble Point Line"
                stroke="#1E90FF" /* DodgerBlue */
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            )}
            {dewPoints.length > 0 && (
              <Line
                type="monotone"
                data={dewPoints}
                dataKey="pressure"
                name="Dew Point Line"
                stroke="#32CD32" /* LimeGreen */
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            )}

            {criticalPoint && (
              <ReferenceDot
                x={criticalPoint.temperature}
                y={criticalPoint.pressure}
                r={6}
                fill="#FF4500" /* OrangeRed */
                stroke="white"
                strokeWidth={1}
                isFront={true}
                alwaysShow={true}
              >
                <Label value="CP" position="top" fill="#FF4500" fontSize={10} fontWeight="bold" />
              </ReferenceDot>
            )}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h4 className="font-medium text-gray-700 mb-2">Key Envelope Points:</h4>
          <div className="space-y-1">
            {criticalPoint && (
              <>
                <div className="flex justify-between"><span className="text-gray-600">Critical Temp:</span> <span className="font-semibold">{criticalPoint.temperature.toFixed(1)} °F</span></div>
                <div className="flex justify-between"><span className="text-gray-600">Critical Press:</span> <span className="font-semibold">{criticalPoint.pressure.toFixed(0)} psi</span></div>
              </>
            )}
            {cricondentherm !== null && (
                <div className="flex justify-between"><span className="text-gray-600">Cricondentherm (Tmax):</span> <span className="font-semibold">{cricondentherm.toFixed(1)} °F</span></div>
            )}
            {cricondenbar !== null && (
                 <div className="flex justify-between"><span className="text-gray-600">Cricondenbar (Pmax):</span> <span className="font-semibold">{cricondenbar.toFixed(0)} psi</span></div>
            )}
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h4 className="font-medium text-gray-700 mb-2">Region Interpretation:</h4>
          <ul className="list-disc list-inside pl-1 space-y-1 text-gray-600 text-xs">
            <li><strong className="text-gray-700">Inside Envelope:</strong> Two-phase region (Liquid + Vapor).</li>
            <li><strong className="text-gray-700">Left of Bubble Line / Above Envelope:</strong> Subcooled Liquid.</li>
            <li><strong className="text-gray-700">Right of Dew Line / Below Envelope:</strong> Superheated Vapor.</li>
            <li><strong className="text-red-600">CP (Critical Point):</strong> Liquid and Vapor phases are indistinguishable.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PhaseEnvelopeChart;
