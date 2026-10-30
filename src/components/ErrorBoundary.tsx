import React, { Component, ErrorInfo, ReactNode } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home, ChevronDown } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Localised title shown in the error card (e.g. "Module Error: Well Control") */
  fallbackTitle?: string;
  /** Localised label for the retry button — defaults to "Try Again" */
  retryLabel?: string;
  /** Localised label for the home button — defaults to "Return to Dashboard" */
  returnLabel?: string;
  /** Localised body sentence — defaults to English fallback */
  unexpectedFailureMessage?: string;
  /** Localised sentence about data preservation — defaults to English fallback */
  dataPreservedMessage?: string;
  /** Callback invoked on retry / return-to-dashboard */
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  componentStack: string | null;
  stackExpanded: boolean;
}

/**
 * Application-level error boundary.
 *
 * Design decisions:
 *  - Class component: required because only class components support
 *    getDerivedStateFromError / componentDidCatch lifecycle hooks.
 *  - All visible strings are passed as props from the parent so that i18n
 *    is controlled by the I18nProvider above us in the tree.
 *  - In development mode (`import.meta.env.DEV`) the React component stack
 *    is shown in a collapsible <details> block to aid debugging.
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    componentStack: null,
    stackExpanded: false,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("PetroLúmen ErrorBoundary caught an unhandled error:", error, errorInfo);
    // Capture the React component stack for dev-mode display
    this.setState({ componentStack: errorInfo.componentStack ?? null });
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null, componentStack: null, stackExpanded: false });
    this.props.onReset?.();
  };

  private toggleStack = () => {
    this.setState((s) => ({ stackExpanded: !s.stackExpanded }));
  };

  public render() {
    if (this.state.hasError) {
      const {
        fallbackTitle,
        retryLabel = "Try Again",
        returnLabel = "Return to Dashboard",
        unexpectedFailureMessage = "An unexpected failure occurred while rendering this component.",
        dataPreservedMessage = "Your data and parameters have been preserved.",
        onReset,
      } = this.props;

      const isDev = import.meta.env.DEV;

      return (
        <div className="p-6 max-w-2xl mx-auto my-8">
          <Card className="border-destructive/30 bg-destructive/5 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-semibold flex items-center gap-2 text-destructive">
                <AlertTriangle className="w-5 h-5" aria-hidden="true" />
                {fallbackTitle || "Module Execution Error"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {unexpectedFailureMessage}{" "}
                <span className="text-muted-foreground/70">{dataPreservedMessage}</span>
              </p>

              {/* Error message */}
              {this.state.error && (
                <div className="p-3 rounded bg-background border text-xs font-mono text-muted-foreground overflow-x-auto">
                  {this.state.error.message || String(this.state.error)}
                </div>
              )}

              {/* Development-only: collapsible component stack */}
              {isDev && this.state.componentStack && (
                <div className="text-xs">
                  <button
                    onClick={this.toggleStack}
                    className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
                    aria-expanded={this.state.stackExpanded}
                  >
                    <ChevronDown
                      className={`w-3 h-3 transition-transform ${this.state.stackExpanded ? "rotate-180" : ""}`}
                    />
                    Component Stack (dev)
                  </button>
                  {this.state.stackExpanded && (
                    <pre className="mt-2 p-3 rounded bg-background border text-muted-foreground overflow-x-auto whitespace-pre-wrap break-all">
                      {this.state.componentStack}
                    </pre>
                  )}
                </div>
              )}

              <div className="flex items-center gap-3 pt-2">
                <Button variant="default" size="sm" onClick={this.handleRetry} className="gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5" />
                  {retryLabel}
                </Button>
                {onReset && (
                  <Button variant="outline" size="sm" onClick={onReset} className="gap-1.5">
                    <Home className="w-3.5 h-3.5" />
                    {returnLabel}
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
