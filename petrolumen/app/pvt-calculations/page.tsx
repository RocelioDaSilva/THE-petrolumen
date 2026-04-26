import React from 'react';
import { PVTCalculator } from '@/app/components/PVTCalculator'; // Adjusted path
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'PVT Calculations | PetroLúmen',
  description: 'Perform various PVT (Pressure-Volume-Temperature) calculations for reservoir engineering.',
};

const PVTCalculationsPage: React.FC = () => {
  return (
    <div className="container mx-auto py-8 px-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
          PVT Property Calculations
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mt-2">
          Calculate various fluid properties based on pressure, volume, and temperature data.
        </p>
      </header>

      <section>
        <PVTCalculator />
      </section>
    </div>
  );
};

export default PVTCalculationsPage;
