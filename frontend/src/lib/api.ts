import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
});

// Mutable ref to hold the latest getToken function from Clerk.
// Updated synchronously on every render so the interceptor always has access.
let _getToken: (() => Promise<string | null>) | null = null;

export function setClerkTokenGetter(fn: (() => Promise<string | null>) | null) {
  _getToken = fn;
}

// Register interceptor ONCE at module load — never ejected.
// It always reads from the mutable ref, which stays current.
api.interceptors.request.use(async (config) => {
  if (_getToken) {
    try {
      const token = await _getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // Silently fail — backend will return 401 if no token
    }
  }
  return config;
});
