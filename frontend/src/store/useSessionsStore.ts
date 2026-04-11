import { create } from "zustand";
import { api } from "../api";
import type { TelegramMessageResponse, TelegramUserSummary } from "../generated/models";

interface SessionsState {
  users: TelegramUserSummary[];
  selectedSenderId: number | null;
  messages: TelegramMessageResponse[];
  loadingUsers: boolean;
  loadingMessages: boolean;
  error: string | null;
  fetchUsers: () => Promise<void>;
  selectUser: (senderId: number) => Promise<void>;
}

export const useSessionsStore = create<SessionsState>((set) => ({
  users: [],
  selectedSenderId: null,
  messages: [],
  loadingUsers: false,
  loadingMessages: false,
  error: null,

  fetchUsers: async () => {
    set({ loadingUsers: true, error: null });
    try {
      const { data } = await api.getTelegramUsers();
      set({ users: data, loadingUsers: false });
    } catch (err) {
      set({ loadingUsers: false, error: "Failed to load users" });
      console.error(err);
    }
  },

  selectUser: async (senderId: number) => {
    set({ selectedSenderId: senderId, loadingMessages: true, error: null });
    try {
      const { data } = await api.getTelegramUserMessages(senderId);
      set({ messages: data, loadingMessages: false });
    } catch (err) {
      set({ loadingMessages: false, error: "Failed to load messages" });
      console.error(err);
    }
  },
}));
