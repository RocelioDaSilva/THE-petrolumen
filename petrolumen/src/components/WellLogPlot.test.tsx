import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WellLogPlot } from './WellLogPlot';
import * as backendClient from '@/lib/backendClient';

vi.mock('@/lib/backendClient', async () => {
  const actual = await vi.importActual('@/lib/backendClient');
  return {
    ...actual,
    parseLasFile: vi.fn(),
  };
});

// Mock Recharts ResponsiveContainer to render children
vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 600 }}>{children}</div>
    ),
  };
});

describe('WellLogPlot Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload empty state when no initial data provided', () => {
    render(<WellLogPlot wellId="TEST-WELL-001" />);

    expect(screen.getByText(/Upload LAS Well Log File/i)).toBeInTheDocument();
    expect(screen.getByText(/Parse & Visualize Log/i)).toBeInTheDocument();
  });

  it('renders parsed well log data when initialData is provided', () => {
    const sampleData = {
      well_name: 'ALPHA-01',
      metadata: {
        FLD: { value: 'GAIA FIELD', unit: '', description: '' },
        COMP: { value: 'PETROLUMEN', unit: '', description: '' },
        API: { value: '42-123-45678', unit: '', description: '' },
      },
      curves: {
        DEPT: { mnemonic: 'DEPT', unit: 'M', description: 'DEPTH', data: [1000, 1001] },
        GR: { mnemonic: 'GR', unit: 'API', description: 'GAMMA RAY', data: [45.2, 52.0] },
      },
      tracks: {
        track1: { title: 'Track 1', curves: ['GR'] },
        track2: { title: 'Track 2', curves: ['ILD'] },
        track3: { title: 'Track 3', curves: ['NPHI'] },
        other: { title: 'Other', curves: [] },
      },
      records: [
        { DEPT: 1000, GR: 45.2 },
        { DEPT: 1001, GR: 52.0 },
      ],
      summary: {
        well_name: 'ALPHA-01',
        start_depth: 1000,
        stop_depth: 1001,
        step: 1,
        null_value: '-999.25',
        curve_count: 2,
        record_count: 2,
        curve_list: ['DEPT', 'GR'],
      },
    };

    render(<WellLogPlot wellId="ALPHA-01" initialData={sampleData} />);

    expect(screen.getByText('ALPHA-01')).toBeInTheDocument();
    expect(screen.getByText(/Field: GAIA FIELD/i)).toBeInTheDocument();
    expect(screen.getByText(/Multi-Track Well Log Interpretation Plot/i)).toBeInTheDocument();
  });

  it('handles LAS file parsing failure gracefully with error state and retry', async () => {
    vi.mocked(backendClient.parseLasFile).mockRejectedValueOnce(new Error('Corrupted LAS header'));

    render(<WellLogPlot wellId="FAIL-WELL" />);

    const fileInput = screen.getByLabelText(/Select LAS File/i);
    const fakeFile = new File(['dummy content'], 'corrupt.las', { type: 'text/plain' });

    fireEvent.change(fileInput, { target: { files: [fakeFile] } });
    const parseBtn = screen.getByRole('button', { name: /Parse & Visualize Log/i });
    fireEvent.click(parseBtn);

    await waitFor(() => {
      expect(screen.getByText(/Well Log Ingestion Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Corrupted LAS header/i)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
  });
});
