import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SessionRegistryProvider, useSessionRegistry } from '../sessionRegistry';

describe('SessionRegistry Context & State Isolation', () => {
  it('throws an error when useSessionRegistry is called outside provider', () => {
    expect(() => {
      renderHook(() => useSessionRegistry());
    }).toThrow(/useSessionRegistry must be called inside a <SessionRegistryProvider>/i);
  });

  it('provides default baseline scenarios within provider', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SessionRegistryProvider>{children}</SessionRegistryProvider>
    );

    const { result } = renderHook(() => useSessionRegistry(), { wrapper });

    expect(result.current.activeScenario).toBeDefined();
    expect(result.current.scenarios.length).toBeGreaterThanOrEqual(3);
    expect(result.current.activeScenario.parameters.wellDepthFt).toBeGreaterThan(0);
  });

  it('allows creating, selecting and cloning scenarios with isolated parameters', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SessionRegistryProvider>{children}</SessionRegistryProvider>
    );

    const { result } = renderHook(() => useSessionRegistry(), { wrapper });

    // Create scenario
    let newScenario: any;
    act(() => {
      newScenario = result.current.createScenario('Test Scenario Alpha', 'Campos Basin');
    });

    expect(result.current.activeScenario.id).toBe(newScenario.id);
    expect(result.current.activeScenario.name).toBe('Test Scenario Alpha');

    // Update parameters in active scenario
    act(() => {
      result.current.updateActiveParameters({ wellDepthFt: 14200 });
    });

    expect(result.current.activeScenario.parameters.wellDepthFt).toBe(14200);

    // Baseline scenarios should not have been mutated
    const baseline = result.current.scenarios.find((s) => !s.isCustom);
    expect(baseline?.parameters.wellDepthFt).not.toBe(14200);
  });
});
