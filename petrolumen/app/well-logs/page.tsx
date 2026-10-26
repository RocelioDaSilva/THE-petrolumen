'use client';

import React from 'react';
import { WellLogPlot } from '@/src/components/WellLogPlot';

export default function WellLogsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <WellLogPlot />
    </div>
  );
}
