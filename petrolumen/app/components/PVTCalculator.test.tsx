import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PVTCalculator } from './PVTCalculator';
import { backendClient, ApiErrorResponse } from '@/lib/backendClient';

vi.mock('@/lib/backendClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/backendClient')>();
  return {
    ...actual,
    backendClient: {
      ...actual.backendClient,
      calculateZFactor: vi.fn(),
      calculateFormationVolumeFactor: vi.fn(),
      calculateViscosity: vi.fn(),
      calculateSolutionGasRatio: vi.fn(),
    },
  };
});

describe('PVTCalculator Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Render State', () => {
    it('mounts without crashing and renders all primary calculator titles and input fields', () => {
      render(<PVTCalculator />);

      expect(screen.getByText('Z-Factor Calculator')).toBeInTheDocument();
      expect(screen.getByText('Formation Volume Factor (FVF) Calculator')).toBeInTheDocument();
      expect(screen.getByText('Viscosity Calculator')).toBeInTheDocument();
      expect(screen.getByText('Solution Gas-Oil Ratio (Rs) Calculator')).toBeInTheDocument();

      expect(screen.getByLabelText(/pressure \(psia\)/i, { selector: '#z_pressure' })).toBeInTheDocument();
      expect(screen.getByLabelText(/temperature \(°f\)/i, { selector: '#z_temperature' })).toBeInTheDocument();
      expect(screen.getByLabelText(/gas specific gravity/i, { selector: '#z_gas_specific_gravity' })).toBeInTheDocument();

      expect(screen.getByRole('button', { name: /calculate z-factor/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /calculate fvf/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /calculate viscosity/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /calculate rs/i })).toBeInTheDocument();
    });
  });

  describe('Primary Interaction', () => {
    it('updates input values and fires API call on submitting Z-Factor form', async () => {
      const user = userEvent.setup();
      vi.mocked(backendClient.calculateZFactor).mockResolvedValueOnce({ z_factor: 0.8542 });

      render(<PVTCalculator />);

      const pressureInput = screen.getByLabelText(/pressure \(psia\)/i, { selector: '#z_pressure' });
      fireEvent.change(pressureInput, { target: { name: 'pressure', value: '1500' } });

      const submitBtn = screen.getByRole('button', { name: /calculate z-factor/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(backendClient.calculateZFactor).toHaveBeenCalledWith({
          pressure: 1500,
          temperature: 150,
          gas_specific_gravity: 0.65,
        });
      });

      expect(await screen.findByText(/Result: Z-Factor = 0.8542/i)).toBeInTheDocument();
    });

    it('submits solution gas ratio form successfully and renders result', async () => {
      const user = userEvent.setup();
      vi.mocked(backendClient.calculateSolutionGasRatio).mockResolvedValueOnce({ rs: 450.5 });

      render(<PVTCalculator />);

      const submitBtn = screen.getByRole('button', { name: /calculate rs/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(backendClient.calculateSolutionGasRatio).toHaveBeenCalledWith({
          pressure: 1000,
          temperature: 150,
          api_gravity: 35,
          gas_specific_gravity: 0.65,
        });
      });

      expect(await screen.findByText(/Result: Rs = 450.50 scf\/STB/i)).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('displays error message when API call fails with ApiErrorResponse', async () => {
      const user = userEvent.setup();
      vi.mocked(backendClient.calculateZFactor).mockRejectedValueOnce(
        new ApiErrorResponse('Invalid pressure input', 400, 'Invalid pressure input')
      );

      render(<PVTCalculator />);

      const submitBtn = screen.getByRole('button', { name: /calculate z-factor/i });
      await user.click(submitBtn);

      expect(await screen.findByText(/Error: Invalid pressure input/i)).toBeInTheDocument();
    });

    it('displays generic error message when API call throws a standard Error', async () => {
      const user = userEvent.setup();
      vi.mocked(backendClient.calculateViscosity).mockRejectedValueOnce(
        new Error('Network connection failed')
      );

      render(<PVTCalculator />);

      const submitBtn = screen.getByRole('button', { name: /calculate viscosity/i });
      await user.click(submitBtn);

      expect(await screen.findByText(/Error: Network connection failed/i)).toBeInTheDocument();
    });
  });
});
