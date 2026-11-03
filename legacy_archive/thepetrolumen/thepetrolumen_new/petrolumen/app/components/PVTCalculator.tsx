"use client";

import React, { useState, FormEvent } from 'react';
import { backendClient, ApiErrorResponse, ZFactorRequestData, ZFactorResponseData, FormationVolumeFactorRequestData, FormationVolumeFactorResponseData, ViscosityRequestData, ViscosityResponseData, SolutionGasRatioRequestData, SolutionGasRatioResponseData } from '@/lib/backendClient';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Helper type for individual form states
type PVTFormState<T> = {
  data: T;
  result: any | null; // Consider more specific result types if needed
  error: string | null;
  isLoading: boolean;
};

// --- Z-Factor Calculation Form ---
const ZFactorForm: React.FC = () => {
  const [formState, setFormState] = useState<PVTFormState<ZFactorRequestData>>({
    data: { pressure: 1000, temperature: 150, gas_specific_gravity: 0.65 },
    result: null, error: null, isLoading: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormState(prev => ({ ...prev, data: { ...prev.data, [e.target.name]: parseFloat(e.target.value) } }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormState(prev => ({ ...prev, isLoading: true, error: null, result: null }));
    try {
      const res = await backendClient.calculateZFactor(formState.data);
      setFormState(prev => ({ ...prev, result: res, isLoading: false }));
    } catch (err) {
      setFormState(prev => ({ ...prev, error: err instanceof ApiErrorResponse ? (err.detail as string) : (err as Error).message, isLoading: false }));
    }
  };

  return (
    <Card>
      <CardHeader><CardTitle>Z-Factor Calculator</CardTitle></CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><Label htmlFor="z_pressure">Pressure (psia)</Label><Input type="number" name="pressure" id="z_pressure" value={formState.data.pressure} onChange={handleChange} required /></div>
          <div><Label htmlFor="z_temperature">Temperature (°F)</Label><Input type="number" name="temperature" id="z_temperature" value={formState.data.temperature} onChange={handleChange} required /></div>
          <div><Label htmlFor="z_gas_specific_gravity">Gas Specific Gravity</Label><Input type="number" name="gas_specific_gravity" id="z_gas_specific_gravity" value={formState.data.gas_specific_gravity} step="0.01" onChange={handleChange} required /></div>
          <Button type="submit" disabled={formState.isLoading}>{formState.isLoading ? "Calculating..." : "Calculate Z-Factor"}</Button>
          {formState.result && <p className="text-green-600">Result: Z-Factor = {formState.result.z_factor?.toFixed(4)}</p>}
          {formState.error && <p className="text-red-600">Error: {formState.error}</p>}
        </form>
      </CardContent>
    </Card>
  );
};

// --- Formation Volume Factor (FVF) Form ---
const FVFForm: React.FC = () => {
  const [formState, setFormState] = useState<PVTFormState<FormationVolumeFactorRequestData>>({
    data: { pressure: 1000, temperature: 150, fluid_type: 'oil', api_gravity: 35, gas_specific_gravity: 0.65 },
    result: null, error: null, isLoading: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormState(prev => ({ ...prev, data: { ...prev.data, [e.target.name]: e.target.name === 'api_gravity' || e.target.name === 'gas_specific_gravity' ? parseFloat(e.target.value) : e.target.value } }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormState(prev => ({ ...prev, data: { ...prev.data, [name]: value } }));
     // Reset api_gravity if fluid_type changes to 'gas'
     if (name === 'fluid_type' && value === 'gas') {
        setFormState(prev => ({ ...prev, data: { ...prev.data, api_gravity: null } }));
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormState(prev => ({ ...prev, isLoading: true, error: null, result: null }));
    try {
      const dataToSend = { ...formState.data };
      if (dataToSend.fluid_type === 'gas') {
        dataToSend.api_gravity = null; // Ensure api_gravity is not sent for gas
      }
      const res = await backendClient.calculateFormationVolumeFactor(dataToSend);
      setFormState(prev => ({ ...prev, result: res, isLoading: false }));
    } catch (err) {
      setFormState(prev => ({ ...prev, error: err instanceof ApiErrorResponse ? (err.detail as string) : (err as Error).message, isLoading: false }));
    }
  };

  return (
    <Card>
      <CardHeader><CardTitle>Formation Volume Factor (FVF) Calculator</CardTitle></CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><Label htmlFor="fvf_pressure">Pressure (psia)</Label><Input type="number" name="pressure" id="fvf_pressure" value={formState.data.pressure} onChange={handleChange} required /></div>
          <div><Label htmlFor="fvf_temperature">Temperature (°F)</Label><Input type="number" name="temperature" id="fvf_temperature" value={formState.data.temperature} onChange={handleChange} required /></div>
          <div>
            <Label htmlFor="fvf_fluid_type">Fluid Type</Label>
            <Select name="fluid_type" value={formState.data.fluid_type} onValueChange={(value) => handleSelectChange('fluid_type', value)}>
              <SelectTrigger><SelectValue placeholder="Select fluid type" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="oil">Oil</SelectItem>
                <SelectItem value="gas">Gas</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {formState.data.fluid_type === 'oil' && (
            <div><Label htmlFor="fvf_api_gravity">API Gravity (for Oil)</Label><Input type="number" name="api_gravity" id="fvf_api_gravity" value={formState.data.api_gravity || ''} onChange={handleChange} required={formState.data.fluid_type === 'oil'} /></div>
          )}
          <div><Label htmlFor="fvf_gas_specific_gravity">Gas Specific Gravity</Label><Input type="number" name="gas_specific_gravity" id="fvf_gas_specific_gravity" value={formState.data.gas_specific_gravity || ''} step="0.01" onChange={handleChange} required /></div>
          <Button type="submit" disabled={formState.isLoading}>{formState.isLoading ? "Calculating..." : "Calculate FVF"}</Button>
          {formState.result && <p className="text-green-600">Result: FVF = {formState.result.fvf?.toFixed(4)}</p>}
          {formState.error && <p className="text-red-600">Error: {formState.error}</p>}
        </form>
      </CardContent>
    </Card>
  );
};

// --- Viscosity Form ---
const ViscosityForm: React.FC = () => {
    const [formState, setFormState] = useState<PVTFormState<ViscosityRequestData>>({
      data: { pressure: 1000, temperature: 150, fluid_type: 'oil', api_gravity: 35, gas_specific_gravity: 0.65 },
      result: null, error: null, isLoading: false,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setFormState(prev => ({ ...prev, data: { ...prev.data, [name]: parseFloat(value) } }));
    };

    const handleSelectChange = (name: string, value: string) => {
        setFormState(prev => ({ ...prev, data: { ...prev.data, [name]: value } }));
        if (name === 'fluid_type' && value === 'gas') {
            setFormState(prev => ({ ...prev, data: { ...prev.data, api_gravity: null } }));
        }
    };

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setFormState(prev => ({ ...prev, isLoading: true, error: null, result: null }));
      try {
        const dataToSend = { ...formState.data };
        if (dataToSend.fluid_type === 'gas') {
            dataToSend.api_gravity = null;
        }
        const res = await backendClient.calculateViscosity(dataToSend);
        setFormState(prev => ({ ...prev, result: res, isLoading: false }));
      } catch (err) {
        setFormState(prev => ({ ...prev, error: err instanceof ApiErrorResponse ? (err.detail as string) : (err as Error).message, isLoading: false }));
      }
    };

    return (
      <Card>
        <CardHeader><CardTitle>Viscosity Calculator</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label htmlFor="visc_pressure">Pressure (psia)</Label><Input type="number" name="pressure" id="visc_pressure" value={formState.data.pressure} onChange={handleChange} required /></div>
            <div><Label htmlFor="visc_temperature">Temperature (°F)</Label><Input type="number" name="temperature" id="visc_temperature" value={formState.data.temperature} onChange={handleChange} required /></div>
            <div>
              <Label htmlFor="visc_fluid_type">Fluid Type</Label>
              <Select name="fluid_type" value={formState.data.fluid_type} onValueChange={(value) => handleSelectChange('fluid_type', value)}>
                <SelectTrigger><SelectValue placeholder="Select fluid type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="oil">Oil</SelectItem>
                  <SelectItem value="gas">Gas</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formState.data.fluid_type === 'oil' && (
              <div><Label htmlFor="visc_api_gravity">API Gravity (for Oil)</Label><Input type="number" name="api_gravity" id="visc_api_gravity" value={formState.data.api_gravity || ''} onChange={handleChange} required={formState.data.fluid_type === 'oil'} /></div>
            )}
            <div><Label htmlFor="visc_gas_specific_gravity">Gas Specific Gravity</Label><Input type="number" name="gas_specific_gravity" id="visc_gas_specific_gravity" value={formState.data.gas_specific_gravity || ''} step="0.01" onChange={handleChange} required /></div>
            <Button type="submit" disabled={formState.isLoading}>{formState.isLoading ? "Calculating..." : "Calculate Viscosity"}</Button>
            {formState.result && <p className="text-green-600">Result: Viscosity = {formState.result.viscosity?.toFixed(4)} cP</p>}
            {formState.error && <p className="text-red-600">Error: {formState.error}</p>}
          </form>
        </CardContent>
      </Card>
    );
  };

// --- Solution Gas-Oil Ratio (Rs) Form ---
const SolutionGasRatioForm: React.FC = () => {
    const [formState, setFormState] = useState<PVTFormState<SolutionGasRatioRequestData>>({
      data: { pressure: 1000, temperature: 150, api_gravity: 35, gas_specific_gravity: 0.65 },
      result: null, error: null, isLoading: false,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormState(prev => ({ ...prev, data: { ...prev.data, [e.target.name]: parseFloat(e.target.value) } }));
    };

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setFormState(prev => ({ ...prev, isLoading: true, error: null, result: null }));
      try {
        const res = await backendClient.calculateSolutionGasRatio(formState.data);
        setFormState(prev => ({ ...prev, result: res, isLoading: false }));
      } catch (err) {
        setFormState(prev => ({ ...prev, error: err instanceof ApiErrorResponse ? (err.detail as string) : (err as Error).message, isLoading: false }));
      }
    };

    return (
      <Card>
        <CardHeader><CardTitle>Solution Gas-Oil Ratio (Rs) Calculator</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label htmlFor="rs_pressure">Pressure (psia)</Label><Input type="number" name="pressure" id="rs_pressure" value={formState.data.pressure} onChange={handleChange} required /></div>
            <div><Label htmlFor="rs_temperature">Temperature (°F)</Label><Input type="number" name="temperature" id="rs_temperature" value={formState.data.temperature} onChange={handleChange} required /></div>
            <div><Label htmlFor="rs_api_gravity">API Gravity</Label><Input type="number" name="api_gravity" id="rs_api_gravity" value={formState.data.api_gravity} onChange={handleChange} required /></div>
            <div><Label htmlFor="rs_gas_specific_gravity">Gas Specific Gravity</Label><Input type="number" name="gas_specific_gravity" id="rs_gas_specific_gravity" value={formState.data.gas_specific_gravity} step="0.01" onChange={handleChange} required /></div>
            <Button type="submit" disabled={formState.isLoading}>{formState.isLoading ? "Calculating..." : "Calculate Rs"}</Button>
            {formState.result && <p className="text-green-600">Result: Rs = {formState.result.rs?.toFixed(2)} scf/STB</p>}
            {formState.error && <p className="text-red-600">Error: {formState.error}</p>}
          </form>
        </CardContent>
      </Card>
    );
  };

// Main PVTCalculator component
export const PVTCalculator: React.FC = () => {
  return (
    <div className="space-y-6">
      <ZFactorForm />
      <FVFForm />
      <ViscosityForm />
      <SolutionGasRatioForm />
    </div>
  );
};
