import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { authAxios } from "../api";
import type { TokenResponse } from "../generated/models";

interface AuthState {
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state is just null; persist handles loading from localStorage
      token: null,

      login: async (username, password) => {
        const { data } = await authAxios.post<TokenResponse>(
          "/api/auth/login",
          {
            username,
            password,
          },
        );

        // No more manual localStorage.setItem!
        // Just update the state and persist does the rest.
        set({ token: data.access_token });
      },

      logout: () => {
        // No more manual localStorage.removeItem!
        set({ token: null });
      },
    }),
    {
      name: "auth-storage", // Unique name for the item in localStorage
      storage: createJSONStorage(() => localStorage), // Defaults to localStorage
    },
  ),
);
