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
  }, [isSignedIn, getToken]);

  return null;
}
