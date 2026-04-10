import { create } from "zustand";
import { api } from "../api";

interface HelloState {
  message: string;
  loading: boolean;
  error: string | null; // Added error state for better UI control
  fetchAll: () => Promise<void>;
}

export const useHelloStore = create<HelloState>((set) => ({
  message: "",
  loading: false,
  error: null,

  fetchAll: async () => {
    set({ loading: true });
    try {
      // 3. Call the method through the 'api' object and destructure 'data'
      const { data } = await api.getHello();

      set({ message: data.message, loading: false });
    } catch (err) {
      set({ loading: false });
      console.error("Failed to fetch hello", err);
    }
  },
}));
