import { create } from "zustand";

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("clerk-token"),
  setToken: (token) => {
    if (token) {
      localStorage.setItem("clerk-token", token);
    } else {
      localStorage.removeItem("clerk-token");
    }
    set({ token });
  },
}));
