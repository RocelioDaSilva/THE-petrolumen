import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Dot } from 'recharts';

// Custom Dot for single point on chart if only one result
const SinglePointDot = (props) => {
  const { cx, cy, stroke, payload, value } = props;
  if (payload && value !== undefined) { // Check if payload and value exist
    return <Dot cx={cx} cy={cy} r={5} fill={stroke} />;
  }
  return null;
};


const PVTResults = ({ results, isLoading, onExportCSV, onPlot }) => {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <p className="ml-3 text-gray-600">Calculating PVT properties...</p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-500">No PVT results to display.</p>
        <p className="text-sm text-gray-400 mt-1">Enter parameters and click "Calculate" or "Generate Table".</p>
      </div>
    );
  }

  const singleResult = results.length === 1 ? results[0] : null;

  const formatValue = (value, digits = 4) => {
    if (value === null || value === undefined || isNaN(parseFloat(value))) return 'N/A';
    return parseFloat(value).toFixed(digits);
  };

  const handleExport = () => {
    if (onExportCSV) {
        // Convert results to CSV string format
        const headers = Object.keys(results[0]).join(',');
        const rows = results.map(row => Object.values(row).map(val => formatValue(val, 6)).join(',')); // Use more precision for CSV
        const csvString = `${headers}\n${rows.join('\n')}`;
        onExportCSV(csvString);
    } else {
        console.warn("onExportCSV handler not provided to PVTResults component.");
    }
  };


  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 mb-1">PVT Analysis Results</h2>

      {/* Single Point Summary (if applicable) */}
      {singleResult && (
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-lg font-semibold mb-3 text-gray-700">
            Properties at {formatValue(singleResult.pressure, 0)} psi & {formatValue(singleResult.temperature, 0)} °F
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-4 text-sm">
            <div><strong className="text-gray-600">Oil FVF (Bo):</strong> {formatValue(singleResult.oil_fvf)} rb/STB</div>
            <div><strong className="text-gray-600">Gas FVF (Bg):</strong> {formatValue(singleResult.gas_fvf, 6)} rcf/scf</div>
            <div><strong className="text-gray-600">Solution GOR (Rs):</strong> {formatValue(singleResult.solution_gor, 0)} scf/STB</div>
            <div><strong className="text-gray-600">Oil Visc. (μo):</strong> {formatValue(singleResult.oil_viscosity, 3)} cp</div>
            <div><strong className="text-gray-600">Gas Visc. (μg):</strong> {formatValue(singleResult.gas_viscosity, 3)} cp</div>
            <div><strong className="text-gray-600">Oil Density (ρo):</strong> {formatValue(singleResult.oil_density, 2)} lb/ft³</div>
            <div><strong className="text-gray-600">Gas Density (ρg):</strong> {formatValue(singleResult.gas_density, 3)} lb/ft³</div>
            {singleResult.z_vapor !== null && singleResult.z_vapor !== undefined &&
              <div><strong className="text-gray-600">Gas Z-Factor (Zg):</strong> {formatValue(singleResult.z_vapor)}</div>
            }
            {singleResult.z_liquid !== null && singleResult.z_liquid !== undefined &&
              <div><strong className="text-gray-600">Liquid Z-Factor (Zl):</strong> {formatValue(singleResult.z_liquid)}</div>
            }
            {singleResult.surface_tension !== null && singleResult.surface_tension !== undefined &&
              <div><strong className="text-gray-600">Surface Tension (σ):</strong> {formatValue(singleResult.surface_tension, 2)} dynes/cm</div>
            }
          </div>
        </div>
      )}

      {/* Charts (if multiple results for table) */}
      {results.length > 1 && (
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-lg font-semibold mb-3 text-gray-700">Pressure Relationships at {formatValue(results[0].temperature, 0)} °F</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Oil FVF and Solution GOR Chart */}
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={results} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0"/>
                  <XAxis dataKey="pressure" unit=" psi" name="Pressure" tickFormatter={(val) => parseFloat(val).toFixed(0)} />
                  <YAxis yAxisId="left" unit=" rb/STB" name="Oil FVF" stroke="#4A90E2" />
                  <YAxis yAxisId="right" orientation="right" unit=" scf/STB" name="GOR" stroke="#50E3C2" />
                  <Tooltip formatter={(value, name) => [formatValue(value, name === 'Solution GOR (Rs)' ? 0 : 4), name]} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="oil_fvf" stroke="#4A90E2" name="Oil FVF (Bo)" dot={<SinglePointDot />} activeDot={{ r: 6 }} />
                  <Line yAxisId="right" type="monotone" dataKey="solution_gor" stroke="#50E3C2" name="Solution GOR (Rs)" dot={<SinglePointDot />} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {/* Viscosities Chart */}
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={results} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0"/>
                  <XAxis dataKey="pressure" unit=" psi" name="Pressure" tickFormatter={(val) => parseFloat(val).toFixed(0)} />
                  <YAxis yAxisId="left" unit=" cp" name="Oil Visc." stroke="#F5A623" />
                  <YAxis yAxisId="right" orientation="right" unit=" cp" name="Gas Visc." stroke="#9013FE" />
                  <Tooltip formatter={(value) => formatValue(value, 3)} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="oil_viscosity" stroke="#F5A623" name="Oil Visc. (μo)" dot={<SinglePointDot />} activeDot={{ r: 6 }} />
                  <Line yAxisId="right" type="monotone" dataKey="gas_viscosity" stroke="#9013FE" name="Gas Visc. (μg)" dot={<SinglePointDot />} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Full PVT Table (if multiple results) */}
      {results.length > 1 && (
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-gray-700">Full PVT Table at {formatValue(results[0].temperature,0)} °F</h3>
            <button
                onClick={handleExport}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400"
            >
                Export to CSV
            </button>
          </div>
          <div className="overflow-x-auto max-h-96">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  {Object.keys(results[0]).map(key => (
                    <th key={key} className="px-4 py-2 text-left font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{key.replace(/_/g, ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((row, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50 hover:bg-gray-100'}>
                    {Object.values(row).map((val, i) => (
                      <td key={i} className="px-4 py-2 whitespace-nowrap">{formatValue(val, Object.keys(row)[i] === 'solution_gor' ? 0 : (Object.keys(row)[i] === 'gas_fvf' ? 6 : 4) )}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PVTResults;
