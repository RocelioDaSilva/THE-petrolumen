"use client"

import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function VisualProbe() {
  const [pzData, setPzData] = useState([])
  const [wells, setWells] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const checkConnectivity = async () => {
      setLoading(true)
      try {
        const res = await fetch('http://localhost:8000/api/v1/wells')
        const data = await res.json()
        setWells(data.wells || [])
      } catch (err) {
        console.error("Connectivity check failed:", err)
      } finally {
        setLoading(false)
      }
    }
    checkConnectivity()
  }, [])

  // Minimal dashboard to verify API contract
  return (
    <div className="p-8 font-sans">
      <h1 className="text-2xl font-bold mb-4 text-blue-600">PetroLúmen Visual Probe</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="border p-4 rounded bg-gray-50">
          <h2 className="text-xl font-semibold mb-2">Material Balance Probe (P/Z)</h2>
          <p className="text-sm text-gray-500 mb-4">Verifying API response for P/Z vs Gp</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={pzData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gp" label={{ value: 'Gp (Mscf)', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'P/Z', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line type="monotone" dataKey="pz" stroke="#2563eb" name="P/Z Factor" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="border p-4 rounded bg-gray-50">
          <h2 className="text-xl font-semibold mb-2">Connectivity Probe</h2>
          <p className="text-sm text-gray-500 mb-4">
            Status: {loading ? 'Checking...' : (wells.length > 0 ? 'Connected' : 'No Wells Found')}
          </p>
          <ul className="text-sm space-y-1">
             {wells.map((w: any) => (
               <li key={w.id} className="p-2 bg-white border rounded">{w.name}</li>
             ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
