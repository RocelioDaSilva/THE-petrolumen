"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AdminActionsPanelProps {
  onClearAllData: () => void;
  isLoading: boolean;
}

export const AdminActionsPanel: React.FC<AdminActionsPanelProps> = ({
  onClearAllData,
  isLoading,
}) => {
  // We might want to only show this panel if the user is an admin.
  // This logic would typically use the authStore.
  // For now, just rendering the button.
  // const { user } = useAppStore();
  // if (user?.role !== 'admin') {
  //   return null;
  // }

  return (
    <Card className="mt-8 border-red-300">
      <CardHeader>
          <CardTitle className="text-red-700">Admin Actions</CardTitle>
      </CardHeader>
      <CardContent>
          <Button onClick={onClearAllData} disabled={isLoading} variant="destructive">
              Clear All Backend Well Data (Admin)
          </Button>
      </CardContent>
    </Card>
  );
};
