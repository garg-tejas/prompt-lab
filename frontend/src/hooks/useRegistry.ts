import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/clerk-react";
import { api } from "@/lib/api";

export function useRegistry<T extends { status?: string }>(path: string, poll = false) {
  const { isSignedIn } = useAuth();
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    if (!isSignedIn) { setRows([]); setLoading(false); return; }
    const controller = new AbortController();
    let timer: number | undefined;
    const load = async (silent = false) => {
      if (!silent) setLoading(true);
      try {
        const response = await api.get<T[]>(path, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setRows(response.data);
        setError(false);
        if (poll && response.data.some((row) => row.status === "running" || row.status === "pending")) {
          timer = window.setTimeout(() => load(true), 3000);
        }
      } catch {
        if (!controller.signal.aborted) setError(true);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void load();
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [path, poll, revision, isSignedIn]);
  return { rows, loading, error, refresh, isSignedIn };
}
