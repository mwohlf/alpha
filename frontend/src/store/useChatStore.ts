import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { api } from "../api";
import type { ChatMessage as ApiChatMessage } from "../generated/models";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatState {
  history: ChatMessage[];
  loading: boolean;
  error: string | null;
  selectedModel: string | null;
  setSelectedModel: (model: string | null) => void;
  sendMessage: (message: string) => Promise<void>;
  clearHistory: () => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      history: [],
      loading: false,
      error: null,
      selectedModel: null,

      setSelectedModel: (model) => set({ selectedModel: model }),

      sendMessage: async (message: string) => {
        const { history, selectedModel } = get();
        const userMessage: ChatMessage = { role: "user", content: message };
        set({ history: [...history, userMessage], loading: true, error: null });

        try {
          const { data } = await api.chatMessageApiChatMessagePost({
            message,
            history: history as ApiChatMessage[],
            model: selectedModel ?? undefined,
          });
          const assistantMessage: ChatMessage = {
            role: "assistant",
            content: data.reply,
          };
          set((s) => ({
            history: [...s.history, assistantMessage],
            loading: false,
          }));
        } catch {
          set((s) => ({
            loading: false,
            error: "Failed to get response",
            history: s.history.slice(0, -1),
          }));
        }
      },

      clearHistory: () => set({ history: [], error: null }),
    }),
    { name: "ChatStore" },
  ),
);
