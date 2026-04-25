import { create } from "zustand";
import { devtools, persist, createJSONStorage } from "zustand/middleware";
import { getAlphaAPI } from "../generated/endpoints";

const loginApi = getAlphaAPI();

interface AuthState {
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        token: null,

        login: async (username, password) => {
          const { data } = await loginApi.login({ username, password });
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
    { name: "AuthStore" },
  ),
);
