import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingSkeletonProps {
  label?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ label = "Carregando módulo..." }) => {
  return (
    <div className="w-full h-96 flex flex-col items-center justify-center space-y-4 rounded-xl border border-dashed border-border/70 bg-card/40 p-8 backdrop-blur-sm animate-pulse">
      <div className="flex items-center gap-3 text-muted-foreground">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
        <span className="text-sm font-medium tracking-wide">{label}</span>
      </div>
      <div className="w-full max-w-md space-y-3 pt-2">
        <div className="h-4 bg-muted/60 rounded-full w-3/4 mx-auto" />
        <div className="h-4 bg-muted/40 rounded-full w-1/2 mx-auto" />
      </div>
    </div>
  );
};

export default LoadingSkeleton;
