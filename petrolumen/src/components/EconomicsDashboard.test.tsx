import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EconomicsDashboard } from './EconomicsDashboard';
import * as backendClient from '@/lib/backendClient';

vi.mock('@/lib/backendClient', async () => {
  const actual = await vi.importActual('@/lib/backendClient');
  return {
    ...actual,
    evaluateEconomicsAdvanced: vi.fn(),
    runEconomicsSensitivity: vi.fn(),
  };
});

// Mock Recharts ResponsiveContainer to render children
vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 400 }}>{children}</div>
    ),
  };
});

describe('EconomicsDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('mounts and executes economic evaluation automatically', async () => {
    const mockEvalResponse = {
      npv: 1250000,
      irr: 0.285,
      payout_period: 4.2,
      payout_months: 4.2,
      payout_years: 0.35,
      total_gross_revenue: 3500000,
      total_net_revenue: 3062500,
      total_opex: 450000,
      total_capex: 2000000,
      total_net_cash_flow: 1800000,
      profitability_index: 1.625,
      return_on_investment: 0.9,
      cash_flow_periods: [
        {
          period: 0,
          time: 0,
          oil_volume: 0,
          gas_volume: 0,
          water_volume: 0,
          oil_price: 70,
          gas_price: 3.5,
          gross_revenue: 0,
          net_revenue: 0,
          opex: 0,
          severance_tax: 0,
          ebitda: 0,
          taxable_income: 0,
          income_tax: 0,
          capex: 2000000,
          net_cash_flow: -2000000,
          cumulative_net_cash_flow: -2000000,
          discount_factor: 1,
          discounted_cash_flow: -2000000,
          cumulative_discounted_cash_flow: -2000000,
        },
      ],
      cash_flows: [-2000000],
      cumulative_cash_flow: [-2000000],
      discounted_cash_flows: [-2000000],
    };

    vi.mocked(backendClient.evaluateEconomicsAdvanced).mockResolvedValueOnce(mockEvalResponse);
    vi.mocked(backendClient.runEconomicsSensitivity).mockResolvedValueOnce({
      type: 'tornado',
      tornado_data: [],
    });

    render(<EconomicsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Economics & Decision Analysis Engine')).toBeInTheDocument();
      expect(screen.getByText('$1,250,000')).toBeInTheDocument();
      expect(screen.getByText('28.50%')).toBeInTheDocument();
      expect(screen.getByText('4.2 mo')).toBeInTheDocument();
    });
  });

  it('handles evaluation errors with retry capability', async () => {
    vi.mocked(backendClient.evaluateEconomicsAdvanced).mockRejectedValueOnce(
      new Error('API Server Unavailable')
    );

    render(<EconomicsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('API Server Unavailable')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
    });
  });
});
