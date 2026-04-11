import axios from "axios";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { TokenResponse } from "../generated/models";

interface AuthState {
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,

      login: async (username, password) => {
        const { data } = await axios.post<TokenResponse>("/api/auth/login", {
          username,
          password,
        });
        set({ token: data.access_token });
      },

      logout: () => {
        set({ token: null });
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
