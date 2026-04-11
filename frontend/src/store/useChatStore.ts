import { create } from "zustand";
import { authAxios } from "../api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatState {
  history: ChatMessage[];
  loading: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearHistory: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  history: [],
  loading: false,
  error: null,

  sendMessage: async (message: string) => {
    const history = get().history;
    const userMessage: ChatMessage = { role: "user", content: message };
    set({ history: [...history, userMessage], loading: true, error: null });

    try {
      const { data } = await authAxios.post<{ reply: string }>("/api/chat/message", {
        message,
        history,
      });
      const assistantMessage: ChatMessage = { role: "assistant", content: data.reply };
      set((s) => ({ history: [...s.history, assistantMessage], loading: false }));
    } catch {
      set((s) => ({ loading: false, error: "Failed to get response", history: s.history.slice(0, -1) }));
    }
  },

  clearHistory: () => set({ history: [], error: null }),
}));
