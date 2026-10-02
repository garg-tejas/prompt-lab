import { useEffect, useState } from "react";

type Listener = (message: string) => void;

let listener: Listener | null = null;

export function notify(message: string) {
  listener?.(message);
}

export function NoticeHost() {
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    listener = setMessage;
    return () => {
      if (listener === setMessage) listener = null;
    };
  }, []);

  if (!message) return null;

  return (
    <div
      role="status"
      className="fixed bottom-4 right-4 z-50 max-w-sm rounded-md border border-border bg-card px-4 py-3 text-sm shadow-none"
    >
      <div className="flex items-start justify-between gap-4">
        <p>{message}</p>
        <button className="font-mono text-xs text-muted-foreground" onClick={() => setMessage(null)}>
          Dismiss
        </button>
      </div>
    </div>
  );
}
