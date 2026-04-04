import { create } from "zustand";
// 1. Import the wrapper function
import { getAlphaAPI } from "../generated/endpoints";

// 2. Initialize the API instance (outside the store)
const api = getAlphaAPI();

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
