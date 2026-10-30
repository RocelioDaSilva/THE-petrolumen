import React, { Component, ErrorInfo, ReactNode } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("PetroLúmen ErrorBoundary caught an unhandled error:", error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 max-w-2xl mx-auto my-8">
          <Card className="border-destructive/30 bg-destructive/5 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-semibold flex items-center gap-2 text-destructive">
                <AlertTriangle className="w-5 h-5" />
                {this.props.fallbackTitle || "Erro na Execução do Módulo"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Ocorreu uma falha inesperada durante a renderização deste componente. Seus dados e parâmetros foram preservados.
              </p>
              {this.state.error && (
                <div className="p-3 rounded bg-background border text-xs font-mono text-muted-foreground overflow-x-auto">
                  {this.state.error.message || String(this.state.error)}
                </div>
              )}
              <div className="flex items-center gap-3 pt-2">
                <Button variant="default" size="sm" onClick={this.handleRetry} className="gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5" />
                  Tentar Novamente
                </Button>
                {this.props.onReset && (
                  <Button variant="outline" size="sm" onClick={this.props.onReset} className="gap-1.5">
                    <Home className="w-3.5 h-3.5" />
                    Voltar ao Painel Geral
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
