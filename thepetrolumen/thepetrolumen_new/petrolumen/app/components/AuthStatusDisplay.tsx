"use client";

import React from 'react';
import { useAppStore, UserProfile } from '@/stores/appStore';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const AuthStatusDisplay: React.FC = () => {
  const { isAuthenticated, user, login, logout } = useAppStore();

  return (
    <Card className="mb-5 bg-slate-50">
      <CardHeader>
        <CardTitle>Auth Status (Zustand Store)</CardTitle>
      </CardHeader>
      <CardContent>
        {isAuthenticated && user ? (
          <div>
            <p>Status: Logged In</p>
            <p>User: {user.username} (Role: {user.role})</p>
            <Button onClick={logout} variant="destructive" size="sm" className="mt-2">Dummy Logout</Button>
          </div>
        ) : (
          <div>
            <p>Status: Logged Out</p>
            <Button
              onClick={() => {
                const dummyUser: UserProfile = {
                    id: 1,
                    username: 'demouser',
                    email: 'demo@example.com',
                    full_name: 'Demo User',
                    role: 'user',
                    is_active: true
                };
                login(dummyUser, 'dummy-auth-token-123');
              }}
              variant="outline"
              size="sm"
              className="mt-2 bg-green-100 hover:bg-green-200"
            >
              Dummy Login
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
