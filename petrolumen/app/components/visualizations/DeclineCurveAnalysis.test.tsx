import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DeclineCurveAnalysis from './DeclineCurveAnalysis';
import { getWellDCA, WellDCAResponse } from '@/lib/backendClient';

vi.mock('@/lib/backendClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/backendClient')>();
  return {
    ...actual,
    getWellDCA: vi.fn(),
  };
});

// Mock recharts components since JS DOM doesn't render SVG / canvas / offset dimensions properly
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('DeclineCurveAnalysis Component', () => {
  const mockDCAResponse: WellDCAResponse = {
    well_name: 'Well-A',
    method_used: 'hyperbolic',
    fitted_params: {
      qi: 1200.5,
      Di: 0.1523,
      b: 0.5,
      type: 'hyperbolic',
    },
    original_data: [
      { date: '2023-01-01', time: 0, rate: 1200 },
      { date: '2023-02-01', time: 31, rate: 1100 },
    ],
    forecast_data: [
      { date: '2023-03-01', time: 59, rate: 1010 },
      { date: '2023-04-01', time: 90, rate: 930 },
    ],
    eur: 2500000,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Render State', () => {
    it('renders empty message when no wellName is provided', () => {
      render(<DeclineCurveAnalysis wellName="" />);
      expect(screen.getByText('Select a well to view decline curve analysis.')).toBeInTheDocument();
      expect(getWellDCA).not.toHaveBeenCalled();
    });

    it('renders header, controls, and triggers DCA fetch when wellName is provided', async () => {
      vi.mocked(getWellDCA).mockResolvedValueOnce(mockDCAResponse);

      render(<DeclineCurveAnalysis wellName="Well-A" />);

      expect(screen.getByText(/Decline Curve Analysis: Well-A/i)).toBeInTheDocument();
      expect(screen.getByText('Arps decline model fitting and EUR prediction')).toBeInTheDocument();

      await waitFor(() => {
        expect(getWellDCA).toHaveBeenCalledWith('Well-A', 'hyperbolic');
      });

      expect(await screen.findByRole('button', { name: /refresh/i })).toBeInTheDocument();
    });
  });

  describe('Primary Interaction', () => {
    it('displays fitted parameters and EUR after successful data fetch', async () => {
      vi.mocked(getWellDCA).mockResolvedValueOnce(mockDCAResponse);

      render(<DeclineCurveAnalysis wellName="Well-A" />);

      await waitFor(() => {
        expect(screen.getByText('1200.50')).toBeInTheDocument();
        expect(screen.getByText('0.1523')).toBeInTheDocument();
        expect(screen.getByText('0.50')).toBeInTheDocument();
        expect(screen.getByText('2.50 MMbbl')).toBeInTheDocument();
      });
    });

    it('refetches DCA when Refresh button is clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(getWellDCA).mockResolvedValue(mockDCAResponse);

      render(<DeclineCurveAnalysis wellName="Well-A" />);

      const refreshBtn = await screen.findByRole('button', { name: /refresh/i });
      await user.click(refreshBtn);

      await waitFor(() => {
        expect(getWellDCA).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error State', () => {
    it('displays error message and Try Again button when DCA fetch fails', async () => {
      vi.mocked(getWellDCA).mockRejectedValueOnce(new Error('DCA computation failed'));

      render(<DeclineCurveAnalysis wellName="Well-A" />);

      expect(await screen.findByText('Error: DCA computation failed')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('retries fetch when Try Again button is clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(getWellDCA)
        .mockRejectedValueOnce(new Error('Initial error'))
        .mockResolvedValueOnce(mockDCAResponse);

      render(<DeclineCurveAnalysis wellName="Well-A" />);

      const retryBtn = await screen.findByRole('button', { name: /try again/i });
      await user.click(retryBtn);

      await waitFor(() => {
        expect(screen.getByText('2.50 MMbbl')).toBeInTheDocument();
      });
    });
  });
});
