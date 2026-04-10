import { create } from "zustand";
import { authAxios } from "../api";
import type { TokenResponse } from "../generated/models";

interface AuthState {
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("access_token"),

  login: async (username, password) => {
    const { data } = await authAxios.post<TokenResponse>("/api/auth/login", { username, password });
    localStorage.setItem("access_token", data.access_token);
    set({ token: data.access_token });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    set({ token: null });
  },
}));
