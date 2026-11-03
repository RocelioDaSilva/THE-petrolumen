"use client";

import React, { useState, FormEvent } from 'react';
import { useAppStore, UserProfile } from '@/stores/appStore';
import { backendClient, ApiErrorResponse, UserProfileResponse } from '@/lib/backendClient';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export const LoginForm: React.FC = () => {
  const { login, isAuthenticated } = useAppStore();
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // 1. Authenticate and get token (token is now set as an HttpOnly cookie by the backend)
      // The response from loginForAccessToken might change; assuming it still returns something
      // or we might not need its direct response if backend confirms session via cookie.
      await backendClient.loginForAccessToken(username, password);
      // No token to set in localStorage anymore.

      // 2. Fetch user details. backendClient.getCurrentUser() will use the HttpOnly cookie.
      const userProfileData: UserProfileResponse = await backendClient.getCurrentUser();

      // 3. Update global store by mapping UserProfileResponse to UserProfile (from appStore)
      // The types are very similar; this mapping ensures conformity.
      const userToStore: UserProfile = {
        id: userProfileData.id,
        username: userProfileData.username,
        email: userProfileData.email,
        full_name: userProfileData.full_name || null, // Handles optional full_name from UserProfileResponse
        role: userProfileData.role,
        is_active: userProfileData.is_active,
      };
      login(userToStore); // Pass only user data; token is not handled by client JS here.

      // Clear form (optional)
      // setUsername('');
      // setPassword('');
      // No need to redirect here, parent components will react to isAuthenticated

    } catch (error) { // Changed err to error for clarity
      console.error("Login failed:", error);
      if (error instanceof ApiErrorResponse) {
        // ApiErrorResponse.detail can be a string or an array of error objects (e.g., FastAPI validation errors)
        const message = typeof error.detail === 'string' ? error.detail :
                        Array.isArray(error.detail) ? error.detail.map(d => d.msg).join(', ') :
                        "Login failed. Please check your credentials.";
        setError(message);
      } else if (error instanceof Error) {
        setError(error.message || "An unexpected error occurred during login.");
      } else {
        setError("An unexpected error occurred during login.");
      }
      // No token in localStorage to clear on error
    } finally {
      setIsLoading(false);
    }
  };

  if (isAuthenticated) {
    return null; // Don't show login form if already authenticated
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Login</CardTitle>
        <CardDescription>Enter your credentials to access the application.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="username">Username (or Email)</Label>
            <Input
              id="username"
              type="text" // Could be email if backend supports it for username field
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Logging in..." : "Login"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
