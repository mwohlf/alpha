import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { useAuthStore } from "./useAuthStore";
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

// Module-level — not reactive state
let currentController: AbortController | null = null;
let historyBeforeRequest: ChatMessage[] = [];

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      history: [],
      loading: false,
      error: null,
      selectedModel: null,

      setSelectedModel: (model) => set({ selectedModel: model }),

      sendMessage: async (message: string) => {
        // If a request is already in-flight, cancel it and reuse the pre-request
        // history snapshot so there's no orphaned user message without a reply.
        if (currentController) {
          currentController.abort();
          currentController = null;
          // historyBeforeRequest already holds the right snapshot
        } else {
          historyBeforeRequest = get().history;
        }

        const snapshot = historyBeforeRequest;
        const { selectedModel } = get();
        const userMessage: ChatMessage = { role: "user", content: message };

        set({ history: [...snapshot, userMessage], loading: true, error: null });

        const controller = new AbortController();
        currentController = controller;

        try {
          const token = useAuthStore.getState().token;
          const response = await fetch("/api/chat/stream", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              message,
              history: snapshot as ApiChatMessage[],
              model: selectedModel ?? undefined,
            }),
            signal: controller.signal,
          });

          if (!response.ok) {
            if (response.status === 401) {
              useAuthStore.getState().logout();
              window.location.href = "/app/login";
              return;
            }
            throw new Error(`HTTP ${response.status}`);
          }

          // Add empty assistant placeholder; chunks will fill it in
          set((s) => ({
            history: [...s.history, { role: "assistant" as const, content: "" }],
          }));

          const reader = response.body!.getReader();
          const decoder = new TextDecoder();
          let buf = "";

          outer: while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buf += decoder.decode(value, { stream: true });
            const lines = buf.split("\n");
            buf = lines.pop() ?? "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const data = JSON.parse(line.slice(6)) as {
                content?: string;
                done?: boolean;
                error?: string;
              };
              if (data.error) throw new Error(data.error);
              if (data.content) {
                set((s) => ({
                  history: [
                    ...s.history.slice(0, -1),
                    {
                      role: "assistant" as const,
                      content: (s.history.at(-1)?.content ?? "") + data.content,
                    },
                  ],
                }));
              }
              if (data.done) break outer;
            }
          }

          historyBeforeRequest = get().history;
          set({ loading: false });
        } catch (e: unknown) {
          if (e instanceof Error && e.name === "AbortError") {
            // Intentionally cancelled — new sendMessage call will take over
            return;
          }
          // Real error: drop partial assistant bubble, keep the user message visible
          set((s) => {
            const h = s.history;
            const trimmed = h.at(-1)?.role === "assistant" ? h.slice(0, -1) : h;
            return { loading: false, error: "Failed to get response", history: trimmed };
          });
        } finally {
          if (currentController === controller) {
            currentController = null;
          }
        }
      },

      clearHistory: () => {
        if (currentController) {
          currentController.abort();
          currentController = null;
        }
        historyBeforeRequest = [];
        set({ history: [], error: null, loading: false });
      },
    }),
    { name: "ChatStore" },
  ),
);
