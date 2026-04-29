import { useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { setTokenGetter } from "@/lib/api";

export function AuthSync() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    if (!isSignedIn) {
      setTokenGetter(null);
      return;
    }

    // Register the token getter so axios can fetch a fresh token before each request
    setTokenGetter(() => getToken());
  }, [isSignedIn, getToken]);

  return null;
}
