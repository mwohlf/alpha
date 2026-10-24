import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { api } from "../api";
import type {
  ChatMemoryResponse,
  MediaItemResponse,
} from "../generated/models";

interface MemoryState {
  memories: ChatMemoryResponse[];
  media: MediaItemResponse[];
  loading: boolean;
  error: string | null;
  fetchMemories: () => Promise<void>;
  updateMemory: (chatId: number, facts: string) => Promise<void>;
  refreshMemory: (chatId: number) => Promise<void>;
  fetchMedia: (chatId: number) => Promise<void>;
  openMedia: (mediaId: number) => Promise<void>;
}

export const useMemoryStore = create<MemoryState>()(
  devtools(
    (set) => {
      const replace = (data: ChatMemoryResponse) =>
        set((s) => ({
          memories: s.memories.map((m) =>
            m.chat_id === data.chat_id ? data : m,
          ),
          loading: false,
        }));

      return {
        memories: [],
        media: [],
        loading: false,
        error: null,

        fetchMemories: async () => {
          set({ loading: true, error: null });
          try {
            const { data } = await api.getMemories();
            set({ memories: data, loading: false });
          } catch {
            set({ loading: false, error: "Failed to load memories" });
          }
        },

        updateMemory: async (chatId, facts) => {
          set({ loading: true, error: null });
          try {
            const { data } = await api.updateMemory(chatId, { facts });
            replace(data);
          } catch {
            set({ loading: false, error: "Failed to save memory" });
          }
        },

        refreshMemory: async (chatId) => {
          set({ loading: true, error: null });
          try {
            const { data } = await api.refreshMemory(chatId);
            replace(data);
          } catch {
            set({ loading: false, error: "Failed to update memory from chat" });
          }
        },

        fetchMedia: async (chatId) => {
          set({ media: [] });
          try {
            const { data } = await api.getChatMedia(chatId);
            set({ media: data });
          } catch {
            set({ error: "Failed to load media" });
          }
        },

        // The file needs the auth header, so it is fetched as a blob and opened from
        // an object URL; the tab is opened first so popup blockers allow it.
        openMedia: async (mediaId) => {
          const tab = window.open("", "_blank");
          try {
            const { data } = await api.getMedia(mediaId);
            const url = URL.createObjectURL(data);
            if (tab) tab.location.href = url;
            else window.location.href = url;
            setTimeout(() => URL.revokeObjectURL(url), 60_000);
          } catch {
            tab?.close();
            set({ error: "Failed to open media" });
          }
        },
      };
    },
    { name: "MemoryStore" },
  ),
);
