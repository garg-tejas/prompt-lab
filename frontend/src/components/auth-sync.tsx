import { useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { setAuthToken } from "@/lib/api";

export function AuthSync() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    if (!isSignedIn) {
      setAuthToken(null);
      return;
    }

    const sync = async () => {
      const token = await getToken();
      setAuthToken(token);
    };

    sync();

    // Refresh token every 30 seconds to prevent expiration
    const interval = setInterval(sync, 30000);
    return () => clearInterval(interval);
  }, [isSignedIn, getToken]);

  return null;
}
