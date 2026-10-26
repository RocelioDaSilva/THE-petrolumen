import { create } from 'zustand';

// Define the shape of the user profile
// This should ideally match the UserResponse model from the backend,
// but simplified for frontend use initially.
export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string; // e.g., 'admin', 'user'
  is_active: boolean;
}

// Define the state structure for the store
interface AppState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  token: string | null;
  selectedWell: string | null;
  login: (user: UserProfile, token?: string | null) => void;
  logout: () => void;
  setToken: (token: string | null) => void;
  setSelectedWell: (wellName: string | null) => void;
}

import { backendClient } from '@/lib/backendClient'; // Import backendClient for logout

// Create the store
export const useAppStore = create<AppState>((set) => ({
  // Initial state
  isAuthenticated: false,
  user: null,
  token: null,
  selectedWell: null,

  // Actions
  login: (userData: UserProfile, userToken?: string | null) => {
    if (typeof window !== 'undefined' && userToken) {
      localStorage.setItem('access_token', userToken);
    }
    set({
      isAuthenticated: true,
      user: userData,
      token: userToken || null
    });
  },

  logout: async () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
    set({
      isAuthenticated: false,
      user: null,
      token: null
    });
  },

  setToken: (userToken) => {
    if (typeof window !== 'undefined') {
      if (userToken) {
        localStorage.setItem('access_token', userToken);
      } else {
        localStorage.removeItem('access_token');
      }
    }
    set({ token: userToken });
  },

  setSelectedWell: (wellName) => {
    set({ selectedWell: wellName });
  },
}));

// Example of how to use the store in a component:
// import { useAppStore } from '@/stores/appStore'; // Adjust path as needed
//
// const MyComponent = () => {
//   const { isAuthenticated, user, login, logout } = useAppStore();
//
//   const handleLogin = () => {
//     // Simulate a login
//     const dummyUser: UserProfile = {
//         id: 1,
//         username: 'testuser',
//         email: 'test@example.com',
//         full_name: 'Test User',
//         role: 'user',
//         is_active: true
//     };
//     const dummyToken = 'dummy-jwt-token';
//     login(dummyUser, dummyToken);
//   };
//
//   const handleLogout = () => {
//     logout();
//   };
//
//   return (
//     <div>
//       {isAuthenticated && user ? (
//         <p>Welcome, {user.username}! Role: {user.role}</p>
//       ) : (
//         <p>Please log in.</p>
//       )}
//       <button onClick={handleLogin}>Login</button>
//       <button onClick={handleLogout}>Logout</button>
//     </div>
//   );
// };
//
// Persistence (e.g., with localStorage) can be added using Zustand middleware:
// import { persist, createJSONStorage } from 'zustand/middleware'
//
// export const useAppStore = create(
//   persist<AppState>(
//     (set, get) => ({
//       // ... (initial state and actions same as above)
//     }),
//     {
//       name: 'app-auth-storage', // name of the item in the storage (must be unique)
//       storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
//       // Only persist parts of the state if needed:
//       // partialize: (state) => ({ token: state.token, isAuthenticated: state.isAuthenticated, user: state.user }),
//     }
//   )
// )
// Note: If using localStorage, ensure it's only accessed on the client-side in Next.js
// to avoid issues with SSR/SSG.
// For now, persistence is not implemented but noted for future steps.
