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

      const savedToken = localStorage.getItem('access_token') || currentTokenInStore;
      if (!savedToken) {
        setIsInitializing(false);
        return;
      }

      setToken(savedToken);

      try {
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
          login(userToStore, savedToken);
        } else {
          await logout();
        }
      } catch (error) {
        console.warn("Auth initialization: Token validation failed.", error);
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
