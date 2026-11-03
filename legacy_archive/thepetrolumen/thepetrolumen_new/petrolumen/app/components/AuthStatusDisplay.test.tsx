/// <reference types="vitest/globals" />
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest'; // Vitest's mocking utility
import { AuthStatusDisplay } from './AuthStatusDisplay';
import { useAppStore, UserProfile } from '@/stores/appStore'; // Import the actual store

// Mock the Zustand store
// We need to mock the entire store module because it's used directly in the component.
// The actual implementation of the store will be replaced by this mock.
vi.mock('@/stores/appStore', () => {
  // Mock the store's state and actions
  const mockLogin = vi.fn();
  const mockLogout = vi.fn();

  // This function will be called by Zustand's `create` internally when `useAppStore` is called.
  // We need to return what the hook would return.
  const mockUseAppStore = (selector?: (state: any) => any) => {
    const state = {
      isAuthenticated: false,
      user: null,
      token: null,
      login: mockLogin,
      logout: mockLogout,
      setToken: vi.fn(),
    };
    // If a selector is provided, apply it, otherwise return the whole state.
    // This simplistic approach might need adjustment for complex selectors.
    return selector ? selector(state) : state;
  };

  // Mock the actual hook `useAppStore`
  mockUseAppStore.getState = () => ({ // Provide a mock getState if components use it directly (though usually not)
    isAuthenticated: false,
    user: null,
    token: null,
    login: mockLogin,
    logout: mockLogout,
    setToken: vi.fn(),
  });

  // Mock the store's setter, typically not directly used by components but good for completeness
  mockUseAppStore.setState = vi.fn();


  return {
    useAppStore: vi.fn().mockImplementation(mockUseAppStore), // Default mock implementation
    // Export UserProfile if it's used by the test file directly for type definitions
    UserProfile: undefined, // Or actual type if needed for type checking in test, but usually not necessary for mock
  };
});


describe('AuthStatusDisplay Component', () => {
  // Helper to set the store state for a specific test
  const setStoreState = (state: { isAuthenticated: boolean; user: UserProfile | null; token?: string | null }) => {
    const mockLogin = vi.fn();
    const mockLogout = vi.fn();
    const mockSetToken = vi.fn();

    (useAppStore as any).mockImplementation((selector?: (state: any) => any) => {
      const fullState = {
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token || null,
        login: mockLogin,
        logout: mockLogout,
        setToken: mockSetToken,
      };
      return selector ? selector(fullState) : fullState;
    });
    // Return mocked actions if tests need to spy on them for this specific state
    return { mockLogin, mockLogout, mockSetToken };
  };


  it('renders logged out state correctly', () => {
    setStoreState({ isAuthenticated: false, user: null });
    render(<AuthStatusDisplay />);
    expect(screen.getByText('Status: Logged Out')).toBeInTheDocument();
    expect(screen.getByText('Dummy Login')).toBeInTheDocument();
    expect(screen.queryByText(/Welcome,/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Dummy Logout')).not.toBeInTheDocument();
  });

  it('renders logged in state correctly', () => {
    const mockUser: UserProfile = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'admin',
      is_active: true
    };
    setStoreState({ isAuthenticated: true, user: mockUser });

    render(<AuthStatusDisplay />);
    expect(screen.getByText('Status: Logged In')).toBeInTheDocument();
    expect(screen.getByText(`User: ${mockUser.username} (Role: ${mockUser.role})`)).toBeInTheDocument();
    expect(screen.getByText('Dummy Logout')).toBeInTheDocument();
    expect(screen.queryByText('Dummy Login')).not.toBeInTheDocument();
  });

  it('calls login action when Dummy Login button is clicked', () => {
    const { mockLogin } = setStoreState({ isAuthenticated: false, user: null });
    render(<AuthStatusDisplay />);

    const loginButton = screen.getByText('Dummy Login');
    fireEvent.click(loginButton);

    expect(mockLogin).toHaveBeenCalledTimes(1);
    const expectedUser: UserProfile = {
        id: 1,
        username: 'demouser',
        email: 'demo@example.com',
        full_name: 'Demo User',
        role: 'user',
        is_active: true
    };
    expect(mockLogin).toHaveBeenCalledWith(expectedUser, 'dummy-auth-token-123');
  });

  it('calls logout action when Dummy Logout button is clicked', () => {
    const mockUser: UserProfile = { id: 1, username: 'testuser', email: '', full_name: '', role: 'user', is_active: true };
    const { mockLogout } = setStoreState({ isAuthenticated: true, user: mockUser });
    render(<AuthStatusDisplay />);

    const logoutButton = screen.getByText('Dummy Logout');
    fireEvent.click(logoutButton);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
