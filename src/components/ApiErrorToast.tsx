import { useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  API_DISCONNECTED_EVENT,
  API_RECONNECTED_EVENT,
  type ApiError,
} from "@/lib/api";

export default function ApiErrorToast() {
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const handleDisconnect = (event: Event) => {
      const error = (event as CustomEvent<ApiError>).detail;
      setMessage(error?.detail ?? "The API connection was lost. Check the server and try again.");
    };
    const handleReconnect = () => setMessage(null);

    window.addEventListener(API_DISCONNECTED_EVENT, handleDisconnect);
    window.addEventListener(API_RECONNECTED_EVENT, handleReconnect);
    return () => {
      window.removeEventListener(API_DISCONNECTED_EVENT, handleDisconnect);
      window.removeEventListener(API_RECONNECTED_EVENT, handleReconnect);
    };
  }, []);

  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="fixed right-4 top-4 z-[100] flex max-w-md items-start gap-3 rounded-lg border border-destructive/40 bg-popover p-4 text-popover-foreground shadow-xl"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">API connection lost</p>
        <p className="mt-1 break-words text-xs text-muted-foreground">{message}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0"
        aria-label="Dismiss API connection alert"
        onClick={() => setMessage(null)}
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  );
}
