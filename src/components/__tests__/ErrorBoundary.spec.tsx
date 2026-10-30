import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import ErrorBoundary from '../ErrorBoundary';

const ProblemChild = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Simulated Module Crash in Engineering Engine');
  }
  return <div>Operational Module Content</div>;
};

describe('ErrorBoundary Component', () => {
  it('renders normal children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Operational Module Content')).toBeInTheDocument();
  });

  it('catches crashes and renders localized error card with retry button', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const onReset = vi.fn();

    render(
      <ErrorBoundary
        fallbackTitle="Custom Error Title"
        retryLabel="Tentar de Novo"
        returnLabel="Ir para Dashboard"
        onReset={onReset}
      >
        <ProblemChild shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    expect(screen.getByText(/Simulated Module Crash in Engineering Engine/)).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /Tentar de Novo/i });
    fireEvent.click(retryBtn);
    expect(onReset).toHaveBeenCalledTimes(1);

    consoleErrorSpy.mockRestore();
  });
});
