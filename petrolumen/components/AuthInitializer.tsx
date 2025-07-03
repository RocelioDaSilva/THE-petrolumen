// Using petrolumen/components/ as it's a client component not specific to an app/page route
"use client";

import { useEffect, useState } from 'react';
import { useAppStore, UserProfile } from '@/stores/appStore';
import { backendClient } from '@/lib/backendClient';

const AuthInitializer: React.FC = () => {
  const { login, logout, setToken, token: currentTokenInStore } = useAppStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      if (typeof window === 'undefined') {
        setIsInitializing(false);
        return; // Don't run on server
      }

      const storedToken = localStorage.getItem('authToken');

      if (storedToken) {
        // If token in store is different or not set, update it (e.g. on first load)
        // This also ensures backendClient will use it if it reads from store directly in future.
        // For now, backendClient reads from localStorage, so this setToken call primarily updates store state.
        if (currentTokenInStore !== storedToken) {
            useAppStore.setState({ token: storedToken }); // Set token directly to avoid re-saving to localStorage
        }

        try {
          // Validate token by fetching user profile
          const userProfileData = await backendClient.getCurrentUser(); // This uses the token from localStorage via fetchWithAuth

          const userToStore: UserProfile = {
            id: userProfileData.id,
            username: userProfileData.username,
            email: userProfileData.email,
            full_name: userProfileData.full_name || null,
            role: userProfileData.role,
            is_active: userProfileData.is_active,
          };

          if (userToStore.is_active) {
            login(userToStore, storedToken); // This will also set token in store and localStorage again (idempotent)
          } else {
            // User is inactive, treat as logged out
            logout(); // This clears user, token, isAuthenticated, and localStorage
          }
        } catch (error) {
          console.warn("Auth token validation failed on load:", error);
          logout(); // Clear invalid token and user state
        }
      } else {
        // No token found, ensure logged out state (e.g. if store was persisted differently)
        if (currentTokenInStore) { // If store had a token but localStorage didn't (e.g. after manual clear)
            logout();
        }
      }
      setIsInitializing(false);
    };

    initializeAuth();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  // Optionally, render a loading state or nothing while initializing
  // For now, it does its work in the background.
  // if (isInitializing) {
  //   return <div>Loading authentication state...</div>;
  // }

  return null; // This component does not render anything itself
};

export default AuthInitializer;
