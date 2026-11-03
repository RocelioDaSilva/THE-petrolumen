import React, { useState, useEffect } from 'react';
import { TrashIcon, PencilSquareIcon, PlusCircleIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'; // Using PencilSquare for edit

const ModelManager = ({
    models = [], // Expects { name: string, type: 'black_oil' | 'compositional', created_at?: string, ...other }
    currentModelName,
    onSelectModel,
    onSaveNewModel, // For creating brand new models (name, type)
    onUpdateModel,  // For saving changes to an existing model's parameters
    onDeleteModel
}) => {
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newModelDetails, setNewModelDetails] = useState({ name: '', type: 'black_oil' });
  const [editingModel, setEditingModel] = useState(null); // Stores the model object being edited

  // When editingModel changes, you might want to populate a form with its details.
  // For this manager, we assume editing happens elsewhere, and this just lists/selects/deletes.
  // The onSaveModel from the parent page (pvt-analysis.jsx) will handle data for new/edited models.

  const handleCreateNewToggle = () => {
    setIsCreatingNew(!isCreatingNew);
    setNewModelDetails({ name: '', type: 'black_oil' }); // Reset form
  };

  const handleSaveNew = () => {
    if (!newModelDetails.name.trim()) {
      alert("Model name cannot be empty."); // Simple validation
      return;
    }
    if (models.find(m => m.name === newModelDetails.name.trim())) {
      alert("A model with this name already exists.");
      return;
    }
    onSaveNewModel(newModelDetails); // Parent handles actual creation and data population
    setIsCreatingNew(false);
  };

  // Placeholder for more detailed edit UI if needed within this component
  // const handleEdit = (model) => {
  //   setEditingModel(model);
  //   // Populate a form with model.pvt_data or model.components
  // };

  // const handleSaveEdits = () => {
  //   if (onUpdateModel && editingModel) {
  //     onUpdateModel(editingModel.name, updatedData); // updatedData from edit form
  //     setEditingModel(null);
  //   }
  // };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-3">
        <h2 className="text-xl font-semibold text-gray-700">PVT Model Manager</h2>
        <button
          onClick={handleCreateNewToggle}
          className="flex items-center text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <PlusCircleIcon className="w-5 h-5 mr-2" />
          {isCreatingNew ? 'Cancel Creation' : 'Create New Model'}
        </button>
      </div>

      {isCreatingNew && (
        <div className="mb-6 p-4 border border-blue-200 bg-blue-50 rounded-lg space-y-3">
          <h3 className="text-md font-semibold text-gray-700">New PVT Model</h3>
          <div>
            <label htmlFor="newModelName" className="block text-sm font-medium text-gray-600 mb-1">Model Name</label>
            <input
              type="text"
              id="newModelName"
              value={newModelDetails.name}
              onChange={(e) => setNewModelDetails({ ...newModelDetails, name: e.target.value })}
              placeholder="Enter unique model name"
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="newModelType" className="block text-sm font-medium text-gray-600 mb-1">Model Type</label>
            <select
              id="newModelType"
              value={newModelDetails.type}
              onChange={(e) => setNewModelDetails({ ...newModelDetails, type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="black_oil">Black Oil</option>
              <option value="compositional">Compositional</option>
            </select>
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSaveNew}
              className="flex items-center text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <CheckCircleIcon className="w-5 h-5 mr-1" />
              Save New Model
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Note: After saving, populate Black Oil parameters in the 'Calculation' tab or components in the 'Composition' tab.
          </p>
        </div>
      )}

      <h3 className="text-md font-semibold text-gray-600 mb-3">Available Models</h3>
      <div className="space-y-3 max-h-[calc(100vh-400px)] overflow-y-auto pr-2 -mr-2">
        {models && models.length > 0 ? (
          models.map((model) => (
            <div
              key={model.name}
              className={`p-3 border rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 transition-all duration-150 ease-in-out
                          ${currentModelName === model.name ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:shadow-sm'}`}
            >
              <div className="flex-grow">
                <h4 className={`font-medium ${currentModelName === model.name ? 'text-blue-700' : 'text-gray-800'}`}>{model.name}</h4>
                <p className="text-xs text-gray-500">
                  Type: <span className="capitalize font-medium">{model.type?.replace('_', ' ')}</span>
                  {model.created_at && ` | Created: ${new Date(model.created_at).toLocaleDateString()}`}
                </p>
              </div>

              <div className="flex space-x-2 items-center flex-shrink-0 mt-2 sm:mt-0">
                <button
                  onClick={() => onSelectModel(model.name)}
                  disabled={currentModelName === model.name}
                  className={`text-xs px-3 py-1.5 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-1
                              ${currentModelName === model.name
                                ? 'bg-blue-600 text-white cursor-default'
                                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
                >
                  {currentModelName === model.name ? 'Selected' : 'Select'}
                </button>
                {/* <button
                  onClick={() => console.log('Edit model:', model.name)} // Placeholder for edit action
                  title="Edit model parameters"
                  className="p-1.5 text-gray-500 hover:text-blue-600 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <PencilSquareIcon className="w-5 h-5" />
                </button> */}
                <button
                  onClick={() => {
                    if (window.confirm(`Are you sure you want to delete model "${model.name}"?`)) {
                      onDeleteModel(model.name);
                    }
                  }}
                  title="Delete model"
                  className="p-1.5 text-gray-500 hover:text-red-600 rounded-md hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500 text-center py-4">No saved models. Click "Create New Model" to start.</p>
        )}
      </div>

      {/* Placeholder for editing UI if an 'editingModel' is set */}
      {/* {editingModel && (
        <div className="mt-6 p-4 border rounded-lg bg-gray-50">
          <h3 className="font-semibold mb-3">Editing: {editingModel.name}</h3>
          // Model-specific editor form would go here, pre-filled with editingModel data
          // e.g., if editingModel.type === 'black_oil', show black oil param inputs
          // if editingModel.type === 'compositional', show component editor or link to it
          <div className="flex justify-end space-x-3 mt-4">
            <button onClick={() => setEditingModel(null)} className="px-4 py-2 border rounded-lg text-sm">Cancel</button>
            <button onClick={handleSaveEdits} className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm">Save Changes</button>
          </div>
        </div>
      )} */}
    </div>
  );
};

export default ModelManager;
