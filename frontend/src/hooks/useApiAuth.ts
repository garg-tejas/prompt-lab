import { useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { setClerkTokenGetter } from "@/lib/api";

/**
 * Keeps the axios client pointed at Clerk's current getToken.
 * One interceptor lives on the client; this hook only swaps the getter.
 */
export function useApiAuth() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    if (!isSignedIn) {
      setClerkTokenGetter(null);
      return;
    }
    setClerkTokenGetter(() => getToken());
    return () => setClerkTokenGetter(null);
  }, [getToken, isSignedIn]);
}
