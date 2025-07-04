import React, { useMemo } from 'react';
import { PlusCircleIcon, TrashIcon } from '@heroicons/react/24/outline'; // Ensure Heroicons is installed

const FluidCompositionEditor = ({ composition = [], onChange, onSave }) => {

  const addComponent = () => {
    const newComponent = {
      name: `Comp${composition.length + 1}`,
      molecular_weight: 0,
      critical_pressure: 0,
      critical_temperature: 0,
      acentric_factor: 0,
      critical_volume: 0, // Added
      parachor: 0,        // Added
      mole_fraction: 0
    };
    onChange([...composition, newComponent]);
  };

  const updateComponent = (index, field, value) => {
    const updatedComposition = composition.map((comp, i) =>
      i === index ? { ...comp, [field]: value } : comp
    );

    // Normalize mole fractions if 'mole_fraction' field was changed
    if (field === 'mole_fraction') {
      const totalMoleFraction = updatedComposition.reduce((sum, comp) => sum + parseFloat(comp.mole_fraction || 0), 0);
      if (totalMoleFraction > 0) { // Avoid division by zero if all are zero
        // Temporarily store unnormalized values if user is actively editing
        // Or, normalize directly:
        // updatedComposition.forEach(comp => {
        //   comp.mole_fraction_normalized = (parseFloat(comp.mole_fraction || 0) / totalMoleFraction);
        // });
        // For direct update of mole_fraction, this could be tricky during input.
        // It's often better to normalize on save or display, or have a "Normalize" button.
        // For this example, let's assume we're directly updating and the user manages the sum.
        // A more robust solution would handle partial input and normalization carefully.
      }
    }
    onChange(updatedComposition);
  };

  const removeComponent = (index) => {
    onChange(composition.filter((_, i) => i !== index));
  };

  const totalMoleFraction = useMemo(() => {
    return composition.reduce((sum, comp) => sum + parseFloat(comp.mole_fraction || 0), 0);
  }, [composition]);

  const handleNormalize = () => {
    if (totalMoleFraction > 0) {
      const normalized = composition.map(comp => ({
        ...comp,
        mole_fraction: parseFloat((parseFloat(comp.mole_fraction || 0) / totalMoleFraction).toFixed(5)) // 5 decimal places for precision
      }));
      onChange(normalized);
    }
  };

  const fieldsConfig = [
    { key: 'name', label: 'Component', type: 'text', placeholder: 'e.g., C1', colSpan: 'col-span-2 md:col-span-2' },
    { key: 'mole_fraction', label: 'Mole Frac (zi)', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-1', isMoleFraction: true },
    { key: 'molecular_weight', label: 'MW', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-1' },
    { key: 'critical_temperature', label: 'Tc (°R)', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-2' },
    { key: 'critical_pressure', label: 'Pc (psia)', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-2' },
    { key: 'acentric_factor', label: 'Acentric (ω)', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-2' },
    { key: 'critical_volume', label: 'Vc (ft³/lb-mol)', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-1' },
    { key: 'parachor', label: 'Parachor', type: 'number', step: 'any', colSpan: 'col-span-2 md:col-span-1' },
  ];


  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-2">
        <h2 className="text-xl font-semibold text-gray-700">Fluid Composition Editor</h2>
        <button
          onClick={addComponent}
          className="flex items-center text-sm bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <PlusCircleIcon className="w-5 h-5 mr-1" />
          Add Component
        </button>
      </div>

      <div className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto pr-2 -mr-2"> {/* Adjust max-h as needed */}
        {composition.map((comp, index) => (
          <div key={index} className="p-3 border border-gray-200 rounded-lg shadow-sm bg-gray-50">
            <div className="grid grid-cols-12 gap-x-3 gap-y-2 items-end">
              {fieldsConfig.map(field => (
                <div key={field.key} className={`${field.colSpan}`}>
                  <label htmlFor={`${field.key}-${index}`} className="block text-xs font-medium text-gray-500 mb-1">{field.label}</label>
                  <input
                    type={field.type}
                    id={`${field.key}-${index}`}
                    step={field.step || 'any'}
                    placeholder={field.placeholder || field.label}
                    value={comp[field.key]}
                    onChange={(e) => updateComponent(index, field.key,
                      field.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
                    )}
                    className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              ))}
              <div className="col-span-12 md:col-span-1 flex justify-end md:self-end">
                <button
                  onClick={() => removeComponent(index)}
                  title="Remove component"
                  className="p-2 text-red-500 hover:text-red-700 focus:outline-none"
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {composition.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">No components added yet. Click "Add Component" to start.</p>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200 flex flex-col sm:flex-row justify-between items-center gap-3">
        <div className="text-sm font-medium text-gray-700">
          Total Mole Fraction:
          <span className={`ml-1 ${Math.abs(totalMoleFraction - 1.0) > 1e-4 && totalMoleFraction > 0 ? 'text-red-600 font-bold' : 'text-green-600 font-bold'}`}>
            {totalMoleFraction.toFixed(4)}
          </span>
          {Math.abs(totalMoleFraction - 1.0) > 1e-4 && totalMoleFraction > 0 && (
            <button onClick={handleNormalize} className="ml-2 text-xs text-blue-600 hover:underline">(Normalize)</button>
          )}
        </div>
        <button
          onClick={onSave}
          className="w-full sm:w-auto bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
          disabled={composition.length === 0 || Math.abs(totalMoleFraction - 1.0) > 1e-4}
          title={Math.abs(totalMoleFraction - 1.0) > 1e-4 ? "Total mole fraction must be 1.0 to save" : "Save model"}
        >
          Save Composition Model
        </button>
      </div>
    </div>
  );
};

export default FluidCompositionEditor;
