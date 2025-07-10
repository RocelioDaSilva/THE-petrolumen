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

      // With HttpOnly cookies, we can't directly check for a token.
      // We attempt to fetch user data; if it succeeds, a valid session cookie exists.
      // The `setToken` action from the store is no longer relevant for managing the actual token string.
      // `currentTokenInStore` is also less relevant as the source of truth is the cookie.

      try {
        // Attempt to fetch current user.
        // backendClient.getCurrentUser() will automatically send the HttpOnly cookie.
        const userProfileData = await backendClient.getCurrentUser();

        const userToStore: UserProfile = {
          id: userProfileData.id,
          username: userProfileData.username,
          email: userProfileData.email,
          full_name: userProfileData.full_name || null,
          role: userProfileData.role,
          is_active: userProfileData.is_active,
        };

        if (userToStore.is_active) {
          // Login action in store now only takes userData, token is implicit via cookie
          login(userToStore);
        } else {
          // User is inactive, treat as logged out
          // logout action in store now also calls backendClient.logoutUser() to clear cookie
          await logout();
        }
      } catch (error) {
        // If getCurrentUser fails (e.g., 401 Unauthorized), it means no valid session.
        // ApiErrorResponse might be thrown by backendClient
        console.warn("Auth initialization: No active session or token validation failed.", error);
        // Ensure client state is logged out.
        // logout() already handles clearing store state.
        // If error is not due to auth (e.g. network error), user remains logged out on client.
        await logout();
      }
      setIsInitializing(false);
    };

    initializeAuth();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [login, logout]); // Added login and logout to dependency array as per ESLint best practices

  // Optionally, render a loading state or nothing while initializing
  // For now, it does its work in the background.
  // if (isInitializing) {
  //   return <div>Loading authentication state...</div>;
  // }

  return null; // This component does not render anything itself
};

export default AuthInitializer;
