import { useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { api } from "@/lib/api";

/**
 * Axios request interceptor that attaches a fresh Clerk JWT to every request.
 * Registered inside a React hook so it has access to useAuth() safely.
 * The interceptor is ejected and re-registered when auth state changes.
 */
export function useApiAuth() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    if (!isSignedIn) return;

    const interceptor = api.interceptors.request.use(async (config) => {
      const token = await getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    return () => {
      api.interceptors.request.eject(interceptor);
    };
  }, [getToken, isSignedIn]);
}
