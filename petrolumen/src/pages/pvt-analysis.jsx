import React, { useState, useEffect, useCallback } from 'react';
import PVTInputForm from '../components/pvt/PVTInputForm';
import PVTResultsDisplay from '../components/pvt/PVTResults'; // Renamed for clarity
import FluidCompositionEditor from '../components/pvt/FluidCompositionEditor';
import ModelManager from '../components/pvt/ModelManager';
import PhaseEnvelopeChart from '../components/pvt/PhaseEnvelope'; // Corrected import name

// Assuming pvtService.js is correctly set up as discussed
import {
  fetchPVTCalculation,
  generatePVTTable,
  createBlackOilModel as apiCreateBlackOilModel,
  createCompositionalModel as apiCreateCompositionalModel,
  // Using mock model persistence for now, replace with API calls when backend supports it
  getLocalMockSavedModels, // Renamed from getSavedModels for clarity
  saveLocalMockModel,      // Renamed from saveModel
  deleteLocalMockModel,
  fetchPhaseEnvelope // Already imported by PhaseEnvelopeChart, but good to have service ref here
} from '../services/pvtService';

// Icon imports (ensure @heroicons/react is installed)
import { BeakerIcon, TableCellsIcon, SwatchIcon, CogIcon, ChartBarIcon } from '@heroicons/react/24/outline';


const PVTAnalysisPage = () => {
  const [pvtResults, setPvtResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('input'); // 'input', 'composition', 'models', 'phase_envelope'

  const [savedPvtModels, setSavedPvtModels] = useState([]);
  const [currentPvtModelName, setCurrentPvtModelName] = useState(''); // Name of the active model
  const [currentComposition, setCurrentComposition] = useState([]); // For compositional model editor

  const [refreshPhaseEnvelope, setRefreshPhaseEnvelope] = useState(0); // To trigger PE chart refresh


  // Load saved models on component mount
  const loadModels = useCallback(async () => {
    setIsLoading(true);
    try {
      // Replace with API call when backend model persistence is ready
      const models = await getLocalMockSavedModels();
      setSavedPvtModels(models);
      if (models.length > 0 && !currentPvtModelName) {
        setCurrentPvtModelName(models[0].name); // Select first model by default
      }
    } catch (error) {
      console.error('Failed to load PVT models:', error);
      // Add user-friendly error notification if desired
    } finally {
      setIsLoading(false);
    }
  }, [currentPvtModelName]); // Added currentPvtModelName to potentially re-evaluate default

  useEffect(() => {
    loadModels();
  }, [loadModels]); // Load models once on mount


  const handleSinglePointCalculation = async (formData) => {
    if (!currentPvtModelName && formData.model_type === 'compositional') {
        alert("Please select or create a compositional model first.");
        return;
    }
    if (!currentPvtModelName && formData.model_type === 'black_oil' && !formData.pvt_data) {
        alert("PVT data for black oil model is missing.");
        return;
    }

    setIsLoading(true);
    setPvtResults([]); // Clear previous results
    try {
      // If using a saved model, its data is in savedPvtModels.
      // If it's a temporary calculation with params from form (e.g. black oil),
      // the backend PVTService will create a temporary in-memory model.
      const modelToUse = savedPvtModels.find(m => m.name === currentPvtModelName);
      let modelNameForApi = currentPvtModelName;

      // If it's a black oil calculation and no specific model is selected,
      // or if the selected model is compositional but we are running a BO calc from form
      // (this logic might need refinement based on exact UI flow)
      // For now, assume formData provides all needed for a new BO model if currentPvtModelName isn't a BO model
      if (formData.model_type === 'black_oil' && (!modelToUse || modelToUse.type !== 'black_oil')) {
          // Create a temporary black oil model on the backend for this calculation
          const tempModelName = `temp_bo_${Date.now()}`;
          await apiCreateBlackOilModel({ name: tempModelName, pvt_data: formData.pvt_data });
          modelNameForApi = tempModelName;
      } else if (formData.model_type === 'compositional' && !modelToUse) {
          // This case should be prevented by UI checks earlier
          throw new Error("No compositional model selected for calculation.");
      }


      const response = await fetchPVTCalculation({
        model_name: modelNameForApi,
        pressure: formData.pressure,
        temperature: formData.temperature
      });
      setPvtResults([response]); // API returns single object, wrap in array
    } catch (error) {
      console.error('PVT single point calculation failed:', error.response?.data?.detail || error.message);
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTableGeneration = async (formData) => {
     if (!currentPvtModelName && formData.model_type === 'compositional') {
        alert("Please select or create a compositional model first.");
        return;
    }
     if (!currentPvtModelName && formData.model_type === 'black_oil' && !formData.pvt_data) {
        alert("PVT data for black oil model is missing.");
        return;
    }

    setIsLoading(true);
    setPvtResults([]);
    try {
      const modelToUse = savedPvtModels.find(m => m.name === currentPvtModelName);
      let modelNameForApi = currentPvtModelName;

      if (formData.model_type === 'black_oil' && (!modelToUse || modelToUse.type !== 'black_oil')) {
          const tempModelName = `temp_bo_table_${Date.now()}`;
          await apiCreateBlackOilModel({ name: tempModelName, pvt_data: formData.pvt_data });
          modelNameForApi = tempModelName;
      } else if (formData.model_type === 'compositional' && !modelToUse) {
          throw new Error("No compositional model selected for table generation.");
      }

      const tableData = await generatePVTTable({
        model_name: modelNameForApi,
        pressure_range: formData.pressure_range, // [start, end, step]
        temperature: formData.temperature
      });
      setPvtResults(tableData);
    } catch (error) {
      console.error('PVT table generation failed:', error.response?.data?.detail || error.message);
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveNewPvtModel = async (modelDetails) => { // {name, type} from ModelManager
    setIsLoading(true);
    try {
      let completeModelData;
      if (modelDetails.type === 'black_oil') {
        // For black oil, we might need a default/empty pvt_data structure
        // Or the user fills this in the main input form after creating the name/type
        completeModelData = {
            name: modelDetails.name,
            type: 'black_oil',
            // For now, let's assume pvt_data is added/edited separately after creation
            // Or, ModelManager's "Create" could expand to include basic BO params.
            pvt_data: modelDetails.pvt_data || { /* default BO params */ }
        };
        await apiCreateBlackOilModel({ name: completeModelData.name, pvt_data: completeModelData.pvt_data });
      } else { // compositional
        // For compositional, components are managed in FluidCompositionEditor
        // When saving a "new" comp model, it might just be creating the name/type shell
        // and then user populates components.
        completeModelData = { name: modelDetails.name, type: 'compositional', components: [] }; // Empty components initially
        await apiCreateCompositionalModel({ name: completeModelData.name, components: [] });
      }

      // Use mock save for UI persistence for now
      await saveLocalMockModel(completeModelData);
      await loadModels(); // Refresh list
      setCurrentPvtModelName(completeModelData.name); // Select the new model
      alert(`Model '${completeModelData.name}' created. Populate its parameters if needed.`);
    } catch (error) {
      console.error('Failed to save new PVT model:', error.response?.data?.detail || error.message);
      alert(`Error saving model: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveComposition = async () => { // Called from FluidCompositionEditor
    if (!currentPvtModelName) {
        alert("Please select or create a compositional model first from the Model Manager.");
        return;
    }
    const modelToUpdate = savedPvtModels.find(m => m.name === currentPvtModelName);
    if (!modelToUpdate || modelToUpdate.type !== 'compositional') {
        alert(`Model '${currentPvtModelName}' is not a compositional model or not found.`);
        return;
    }
    if (Math.abs(currentComposition.reduce((s,c)=>s + (c.mole_fraction || 0),0) - 1.0) > 1e-4) {
        alert("Sum of mole fractions must be 1.0 (or very close). Please normalize or adjust.");
        return;
    }

    setIsLoading(true);
    try {
        // Update backend (in-memory for now)
        await apiCreateCompositionalModel({ name: currentPvtModelName, components: currentComposition }); // This effectively overwrites
        // Update mock local storage
        await saveLocalMockModel({ ...modelToUpdate, components: currentComposition });
        await loadModels(); // Refresh (though components aren't shown in list)
        alert(`Composition for model '${currentPvtModelName}' saved successfully.`);
        setRefreshPhaseEnvelope(prev => prev + 1); // Trigger PE chart refresh
    } catch (error) {
        console.error('Failed to save composition:', error.response?.data?.detail || error.message);
        alert(`Error saving composition: ${error.response?.data?.detail || error.message}`);
    } finally {
        setIsLoading(false);
    }
  };

  const handleDeletePvtModel = async (modelName) => {
    setIsLoading(true);
    try {
        // Add API call to delete from backend when implemented
        // For now, just mock:
        await deleteLocalMockModel(modelName);
        await loadModels();
        if (currentPvtModelName === modelName) {
            setCurrentPvtModelName(savedPvtModels.length > 0 ? savedPvtModels[0].name : '');
        }
        alert(`Model '${modelName}' deleted.`);
    } catch (error) {
        console.error('Failed to delete PVT model:', error.response?.data?.detail || error.message);
         alert(`Error deleting model: ${error.response?.data?.detail || error.message}`);
    } finally {
        setIsLoading(false);
    }
  };

  const handleSelectPvtModel = (modelName) => {
    setCurrentPvtModelName(modelName);
    const selectedModel = savedPvtModels.find(m => m.name === modelName);
    if (selectedModel?.type === 'compositional') {
        setCurrentComposition(selectedModel.components || []);
        if (activeTab !== 'phase_envelope') setActiveTab('composition'); // Switch to composition editor
        setRefreshPhaseEnvelope(prev => prev + 1); // Trigger PE chart refresh
    } else if (selectedModel?.type === 'black_oil') {
        // TODO: Pre-fill PVTInputForm with selected black oil model's pvt_data
        if (activeTab !== 'input') setActiveTab('input');
    }
    setPvtResults([]); // Clear results when model changes
  };

  const getSelectedModelType = () => {
    const model = savedPvtModels.find(m => m.name === currentPvtModelName);
    return model ? model.type : 'black_oil'; // Default to black_oil if no model selected
  };

  const TabButton = ({ id, label, icon: Icon }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center justify-center sm:justify-start px-3 py-2.5 text-sm font-medium rounded-md transition-colors duration-150 ease-in-out
                  ${activeTab === id
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'}`}
    >
      <Icon className="w-5 h-5 mr-0 sm:mr-2 flex-shrink-0" />
      <span className="hidden sm:inline">{label}</span>
    </button>
  );

  return (
    <div className="container mx-auto px-2 sm:px-4 py-6">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 pb-4 border-b border-gray-200">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-800">PVT Fluid Analysis</h1>
        {/* Tab buttons for navigation */}
        <div className="flex space-x-1 sm:space-x-2 mt-3 sm:mt-0 p-1 bg-gray-100 rounded-lg shadow-sm">
          <TabButton id="input" label="Calculation" icon={BeakerIcon} />
          <TabButton id="composition" label="Composition" icon={SwatchIcon} />
          <TabButton id="phase_envelope" label="Phase Envelope" icon={ChartBarIcon} />
          <TabButton id="models" label="Models" icon={CogIcon} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel (Inputs/Editors) */}
        <div className="lg:col-span-4 space-y-6">
          {activeTab === 'input' && (
            <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6">
              <div className="mb-4">
                <label htmlFor="currentModelSelect" className="block text-sm font-medium text-gray-700 mb-1">Active PVT Model</label>
                <select
                  id="currentModelSelect"
                  value={currentPvtModelName}
                  onChange={(e) => handleSelectPvtModel(e.target.value)}
                  className="w-full p-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  disabled={isLoading}
                >
                  <option value="">-- Select or Create a Model --</option>
                  {savedPvtModels.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name} ({model.type?.replace('_', ' ')})
                    </option>
                  ))}
                   <option value="" disabled>-------------------------</option>
                   <option value="_new_black_oil_temp">Temporary Black Oil (use form below)</option>
                </select>
              </div>
              <PVTInputForm
                key={currentPvtModelName} // Re-mount form if model changes to reset defaults potentially
                onSubmitSinglePoint={handleSinglePointCalculation}
                onGenerateTable={handleTableGeneration}
                modelType={getSelectedModelType()}
                isLoading={isLoading}
                // Pass current model's black oil data if applicable for pre-fill
                // defaultValues={savedPvtModels.find(m => m.name === currentPvtModelName && m.type === 'black_oil')?.pvt_data}
              />
            </div>
          )}

          {activeTab === 'composition' && (
            <FluidCompositionEditor
              key={currentPvtModelName} // Re-key to reflect changes if model selection affects composition
              composition={currentComposition}
              onChange={setCurrentComposition}
              onSave={handleSaveComposition} // This will save to the currentPvtModelName
            />
          )}

          {activeTab === 'phase_envelope' && (!currentPvtModelName || getSelectedModelType() !== 'compositional') && (
             <div className="bg-white rounded-xl shadow-lg p-6 text-center">
                <p className="text-gray-600 font-medium">Please select or create a Compositional Model from the 'Models' tab to view its phase envelope.</p>
             </div>
          )}

          {activeTab === 'models' && (
            <ModelManager
              models={savedPvtModels}
              currentModelName={currentPvtModelName}
              onSelectModel={handleSelectPvtModel}
              onSaveNewModel={handleSaveNewPvtModel}
              onDeleteModel={handleDeletePvtModel}
              // onUpdateModel would be passed if ModelManager handled editing internally
            />
          )}
        </div>

        {/* Right Panel (Results/Charts) */}
        <div className="lg:col-span-8">
          {activeTab === 'input' && (
            <PVTResultsDisplay
              results={pvtResults}
              isLoading={isLoading}
              onExportCSV={(csvString) => {
                  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
                  const link = document.createElement("a");
                  const url = URL.createObjectURL(blob);
                  link.setAttribute("href", url);
                  link.setAttribute("download", `pvt_results_${currentPvtModelName || 'table'}.csv`);
                  link.style.visibility = 'hidden';
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
              }}
            />
          )}
          {activeTab === 'phase_envelope' && currentPvtModelName && getSelectedModelType() === 'compositional' && (
             <PhaseEnvelopeChart modelName={currentPvtModelName} refreshTrigger={refreshPhaseEnvelope} />
          )}
           {(activeTab === 'composition' || activeTab === 'models') && !isLoading && (
             <div className="bg-white rounded-xl shadow-lg p-6 text-center min-h-[300px] flex flex-col justify-center items-center">
                <TableCellsIcon className="w-16 h-16 text-gray-300 mb-4" />
                <p className="text-gray-500">
                  {activeTab === 'composition' ? "Edit fluid composition for the selected compositional model." : "Manage your saved PVT models here."}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Results and charts will be shown in other tabs once calculations are performed.
                </p>
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

export default PVTAnalysisPage;
