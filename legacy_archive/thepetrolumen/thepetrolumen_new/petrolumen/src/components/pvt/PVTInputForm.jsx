import React, { useState } from 'react';
import { useForm } from 'react-hook-form';

const PVTInputForm = ({ onSubmitSinglePoint, onGenerateTable, modelType = 'black_oil', isLoading, availableModels = [] }) => {
  const { register, handleSubmit, watch, formState: { errors }, reset } = useForm({
    defaultValues: {
      // Default Black Oil parameters (can be adjusted or loaded from selected model)
      temperature: 180, // °F
      pressure_single: 3000, // psi for single point calculation
      gamma_o: 0.85, // Oil specific gravity
      gamma_g: 0.75, // Gas specific gravity
      pb: 2500,       // Bubble point pressure (psi)
      co: 1.8e-5,     // Oil compressibility (1/psi)
      rsb: 750,       // Solution GOR at bubble point (scf/STB)
      bob: 1.42,      // Oil FVF at bubble point (rb/STB)
      muob: 0.85,     // Oil viscosity at bubble point (cp)
      muod: 3.2,      // Dead oil viscosity (cp)
      cg: 3.2e-4,     // Gas compressibility (1/psi) - may not be directly used by correlations
      // For table generation
      pressure_start: 500,
      pressure_end: 5000,
      pressure_step: 500,
      table_temperature: 180,
    }
  });

  const [isTableParamsVisible, setIsTableParamsVisible] = useState(false);

  const currentModelType = watch('modelTypeWatch', modelType); // Watch the prop

  const handleSinglePointSubmit = (data) => {
    const blackOilPvtData = {
        pb: parseFloat(data.pb), co: parseFloat(data.co), rsb: parseFloat(data.rsb), bob: parseFloat(data.bob),
        muob: parseFloat(data.muob), muod: parseFloat(data.muod), cg: parseFloat(data.cg),
        gamma_g: parseFloat(data.gamma_g), gamma_o: parseFloat(data.gamma_o), temperature: parseFloat(data.temperature)
    };
    onSubmitSinglePoint({
        model_type: currentModelType, // black_oil or compositional
        // If compositional, components would be passed separately or identified by model_name
        name: data.modelName || `temp_bo_${Date.now()}`, // Temporary name or selected model
        pvt_data: currentModelType === 'black_oil' ? blackOilPvtData : undefined,
        // components: currentModelType === 'compositional' ? loadedComponents : undefined,
        pressure: parseFloat(data.pressure_single), // For single point calculation
        temperature: parseFloat(data.temperature) // Common temperature for both
    });
  };

  const handleTableSubmit = (data) => {
    const blackOilPvtData = {
        pb: parseFloat(data.pb), co: parseFloat(data.co), rsb: parseFloat(data.rsb), bob: parseFloat(data.bob),
        muob: parseFloat(data.muob), muod: parseFloat(data.muod), cg: parseFloat(data.cg),
        gamma_g: parseFloat(data.gamma_g), gamma_o: parseFloat(data.gamma_o), temperature: parseFloat(data.table_temperature)
    };
    onGenerateTable({
        model_type: currentModelType,
        name: data.modelName || `temp_bo_table_${Date.now()}`,
        pvt_data: currentModelType === 'black_oil' ? blackOilPvtData : undefined,
        pressure_range: [parseFloat(data.pressure_start), parseFloat(data.pressure_end), parseFloat(data.pressure_step)],
        temperature: parseFloat(data.table_temperature)
    });
  };

  // Simplified error rendering
  const renderError = (field) => errors[field] && <p className="text-xs text-red-500 mt-1">{errors[field].message || 'This field is required.'}</p>;

  return (
    <div className="p-1"> {/* Reduced padding if part of a larger card */}
      <h3 className="text-lg font-semibold mb-3 text-gray-700">
        {currentModelType === 'black_oil' ? 'Black Oil Model Parameters' : 'Compositional Model Input'}
      </h3>

      {/* Common Parameters */}
      <div className="mb-4">
        <label htmlFor="temperature" className="block text-sm font-medium text-gray-600 mb-1">Reservoir Temperature (°F)</label>
        <input
          type="number"
          id="temperature"
          step="any"
          className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          {...register('temperature', { required: 'Temperature is required', valueAsNumber: true })}
        />
        {renderError('temperature')}
      </div>

      {currentModelType === 'black_oil' && (
        <>
          <div className="grid grid-cols-2 gap-x-4 gap-y-3 mb-4">
            <div>
              <label htmlFor="gamma_o" className="block text-sm font-medium text-gray-600 mb-1">Oil Specific Gravity (γo)</label>
              <input type="number" id="gamma_o" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('gamma_o', { required: true, valueAsNumber: true, min: { value: 0.5, message: "Min 0.5"}, max: {value: 1.2, message: "Max 1.2"} })} />
              {renderError('gamma_o')}
            </div>
            <div>
              <label htmlFor="gamma_g" className="block text-sm font-medium text-gray-600 mb-1">Gas Specific Gravity (γg)</label>
              <input type="number" id="gamma_g" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('gamma_g', { required: true, valueAsNumber: true, min: { value: 0.5, message: "Min 0.5"}, max: {value: 1.5, message: "Max 1.5"} })} />
              {renderError('gamma_g')}
            </div>
            <div>
              <label htmlFor="pb" className="block text-sm font-medium text-gray-600 mb-1">Bubble Point (Pb, psi)</label>
              <input type="number" id="pb" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('pb', { required: true, valueAsNumber: true })} />
              {renderError('pb')}
            </div>
            <div>
              <label htmlFor="rsb" className="block text-sm font-medium text-gray-600 mb-1">Solution GOR @ Pb (Rsb, scf/STB)</label>
              <input type="number" id="rsb" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('rsb', { required: true, valueAsNumber: true })} />
              {renderError('rsb')}
            </div>
            <div>
              <label htmlFor="bob" className="block text-sm font-medium text-gray-600 mb-1">Oil FVF @ Pb (Bob, rb/STB)</label>
              <input type="number" id="bob" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('bob', { required: true, valueAsNumber: true })} />
              {renderError('bob')}
            </div>
            <div>
              <label htmlFor="co" className="block text-sm font-medium text-gray-600 mb-1">Oil Compressibility (Co, 1/psi)</label>
              <input type="number" id="co" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('co', { required: true, valueAsNumber: true })} />
              {renderError('co')}
            </div>
            <div>
              <label htmlFor="muob" className="block text-sm font-medium text-gray-600 mb-1">Oil Visc. @ Pb (μob, cp)</label>
              <input type="number" id="muob" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('muob', { required: true, valueAsNumber: true })} />
              {renderError('muob')}
            </div>
            <div>
              <label htmlFor="muod" className="block text-sm font-medium text-gray-600 mb-1">Dead Oil Visc. (μod, cp)</label>
              <input type="number" id="muod" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('muod', { required: true, valueAsNumber: true })} />
              {renderError('muod')}
            </div>
             <div>
              <label htmlFor="cg" className="block text-sm font-medium text-gray-600 mb-1">Gas Compressibility (Cg, 1/psi)</label>
              <input type="number" id="cg" step="any" className="w-full p-2 border border-gray-300 rounded-md shadow-sm" {...register('cg', { required: true, valueAsNumber: true })} />
              {renderError('cg')}
            </div>
          </div>
        </>
      )}

      {currentModelType === 'compositional' && (
        <p className="text-sm text-gray-500 mb-4">
          Compositional model parameters are managed in the 'Composition' tab. Select a saved compositional model.
        </p>
      )}

      {/* Single Point Calculation */}
      <form onSubmit={handleSubmit(handleSinglePointSubmit)} className="mb-6 p-4 border border-dashed border-gray-300 rounded-lg">
        <h4 className="text-md font-semibold mb-2 text-gray-700">Single Point Calculation</h4>
        <div className="mb-3">
          <label htmlFor="pressure_single" className="block text-sm font-medium text-gray-600 mb-1">Pressure (psi)</label>
          <input
            type="number"
            id="pressure_single"
            step="any"
            className="w-full p-2 border border-gray-300 rounded-md shadow-sm"
            {...register('pressure_single', { required: 'Pressure is required', valueAsNumber: true })}
          />
          {renderError('pressure_single')}
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isLoading ? 'Calculating...' : 'Calculate Single Point'}
        </button>
      </form>

      {/* Table Generation Toggle and Form */}
      <div className="mb-3">
        <button
          type="button"
          onClick={() => setIsTableParamsVisible(!isTableParamsVisible)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          {isTableParamsVisible ? 'Hide' : 'Show'} PVT Table Generation Options
        </button>
      </div>

      {isTableParamsVisible && (
         <form onSubmit={handleSubmit(handleTableSubmit)} className="p-4 border border-dashed border-gray-300 rounded-lg">
            <h4 className="text-md font-semibold mb-2 text-gray-700">PVT Table Generation</h4>
            <div className="grid grid-cols-3 gap-x-4 gap-y-3 mb-3">
                <div>
                    <label htmlFor="pressure_start" className="block text-sm font-medium text-gray-600 mb-1">Start P (psi)</label>
                    <input type="number" id="pressure_start" step="any" className="w-full p-2 border rounded-md" {...register('pressure_start', {required:true, valueAsNumber:true})} />
                    {renderError('pressure_start')}
                </div>
                <div>
                    <label htmlFor="pressure_end" className="block text-sm font-medium text-gray-600 mb-1">End P (psi)</label>
                    <input type="number" id="pressure_end" step="any" className="w-full p-2 border rounded-md" {...register('pressure_end', {required:true, valueAsNumber:true})} />
                    {renderError('pressure_end')}
                </div>
                <div>
                    <label htmlFor="pressure_step" className="block text-sm font-medium text-gray-600 mb-1">Step P (psi)</label>
                    <input type="number" id="pressure_step" step="any" className="w-full p-2 border rounded-md" {...register('pressure_step', {required:true, valueAsNumber:true, min: {value: 1, message: "Step > 0"}})} />
                    {renderError('pressure_step')}
                </div>
            </div>
             <div className="mb-3">
                <label htmlFor="table_temperature" className="block text-sm font-medium text-gray-600 mb-1">Table Temperature (°F)</label>
                <input type="number" id="table_temperature" step="any" className="w-full p-2 border rounded-md" {...register('table_temperature', {required:true, valueAsNumber:true})} />
                {renderError('table_temperature')}
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              {isLoading ? 'Generating...' : 'Generate PVT Table'}
            </button>
        </form>
      )}
    </div>
  );
};

export default PVTInputForm;
