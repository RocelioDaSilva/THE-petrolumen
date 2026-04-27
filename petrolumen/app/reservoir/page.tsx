'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReservoirPage() {
  const [ogip, setOgip] = useState<number | null>(null);

  const calculateVol = async () => {
    try {
      const res = await axios.post(`${API_URL}/api/v1/gaia/reservoir/ogip-volumetric`, {
        area: 640, thickness: 25, porosity: 0.2, sw: 0.25, bg: 0.005
      });
      setOgip(res.data.ogip);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">Reservoir Volumetrics</h1>
      <Card>
        <CardHeader><CardTitle>Volumetric OGIP Calculator</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">Using default reservoir properties (640 acres, 25 ft net pay, etc.)</p>
          <Button onClick={calculateVol}>Calculate OGIP</Button>
          {ogip && <p className="text-2xl font-bold mt-4 text-primary">OGIP: {(ogip/1e9).toFixed(2)} Bcf</p>}
        </CardContent>
      </Card>
    </div>
  );
}
