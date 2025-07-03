"use client";

import React, { useState, FormEvent } from 'react';
import { useAppStore, UserProfile } from '@/stores/appStore';
import { backendClient, ApiErrorResponse } from '@/lib/backendClient'; // Assuming backendClient has loginUser
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
      // 1. Authenticate and get token
      const tokenResponse = await backendClient.loginForAccessToken(username, password);
      const token = tokenResponse.access_token;

      // Store token immediately for subsequent requests
      // In a real app, use secure storage. For now, localStorage for web or for Zustand store.
      localStorage.setItem('authToken', token); // For backendClient to pick up

      // 2. Fetch user details using the new token
      // backendClient's internal fetch should now use the token from localStorage
      const userProfileData = await backendClient.getCurrentUser(); // This now sends the token

      // 3. Update global store
      // Assuming UserProfile type from store matches backend response structure for /users/me
      const userToStore: UserProfile = {
        id: userProfileData.id, // Assuming id is part of UserResponse from backend
        username: userProfileData.username,
        email: userProfileData.email,
        full_name: userProfileData.full_name || null,
        role: userProfileData.role, // Assuming role is part of UserResponse
        is_active: userProfileData.is_active, // Assuming is_active is part of UserResponse
      };
      login(userToStore, token);

      // Clear form (optional)
      // setUsername('');
      // setPassword('');
      // No need to redirect here, parent components will react to isAuthenticated

    } catch (err) {
      console.error("Login failed:", err);
      if (err instanceof ApiErrorResponse) {
        setError(err.detail || "Login failed. Please check your credentials.");
      } else if (err instanceof Error) {
        setError(err.message || "An unexpected error occurred during login.");
      } else {
        setError("An unexpected error occurred during login.");
      }
      localStorage.removeItem('authToken'); // Clear token on error
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
