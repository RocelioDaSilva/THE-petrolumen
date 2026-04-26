"use client";

import React from 'react';
import { useAppStore, UserProfile } from '@/stores/appStore';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const AuthStatusDisplay: React.FC = () => {
  const { isAuthenticated, user, logout } = useAppStore();

  if (!isAuthenticated || !user) return null;

  return (
    <Card className="mb-5 bg-muted/30">
      <CardHeader className="py-3">
        <CardTitle className="text-sm font-medium">Session Information</CardTitle>
      </CardHeader>
      <CardContent className="py-2">
          <div className="flex items-center justify-between">
            <div>
                <p className="text-sm font-semibold">{user.full_name || user.username}</p>
                <p className="text-xs text-muted-foreground">{user.email} • <span className="uppercase">{user.role}</span></p>
            </div>
            <Button onClick={logout} variant="outline" size="sm">Sign Out</Button>
          </div>
      </CardContent>
    </Card>
  );
};
