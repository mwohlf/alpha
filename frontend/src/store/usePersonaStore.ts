import { create } from "zustand";
import { api } from "../api";
import type { PersonaResponse } from "../generated/models";

interface PersonaState {
  personas: PersonaResponse[];
  loading: boolean;
  error: string | null;
  fetchPersonas: () => Promise<void>;
  createPersona: (name: string, content: string, isActive: boolean) => Promise<void>;
  updatePersona: (id: number, name?: string, content?: string, isActive?: boolean) => Promise<void>;
}

export const usePersonaStore = create<PersonaState>((set) => ({
  personas: [],
  loading: false,
  error: null,

  fetchPersonas: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.getPersonas();
      set({ personas: data, loading: false });
    } catch {
      set({ loading: false, error: "Failed to load personas" });
    }
  },

  createPersona: async (name, content, isActive) => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.createPersona({ name, content, is_active: isActive });
      set((s) => ({
        personas: isActive
          ? [...s.personas.map((p) => ({ ...p, is_active: false })), data]
          : [...s.personas, data],
        loading: false,
      }));
    } catch {
      set({ loading: false, error: "Failed to create persona" });
    }
  },

  updatePersona: async (id, name, content, isActive) => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.updatePersona(id, {
        name,
        content,
        is_active: isActive,
      });
      set((s) => ({
        personas: s.personas.map((p) => {
          if (isActive && p.id !== id) return { ...p, is_active: false };
          return p.id === id ? data : p;
        }),
        loading: false,
      }));
    } catch {
      set({ loading: false, error: "Failed to update persona" });
    }
  },
}));
