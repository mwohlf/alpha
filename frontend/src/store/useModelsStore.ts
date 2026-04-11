import { create } from "zustand";
import { api } from "../api";
import type { OllamaModel } from "../generated/models";

interface ModelsState {
  models: OllamaModel[];
  selected: OllamaModel | null;
  loading: boolean;
  error: string | null;
  fetchModels: () => Promise<void>;
  selectModel: (model: OllamaModel | null) => void;
  deleteModel: (name: string) => Promise<void>;
  addModel: (name: string) => Promise<void>;
}

export const useModelsStore = create<ModelsState>((set, get) => ({
  models: [],
  selected: null,
  loading: false,
  error: null,

  fetchModels: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await api.getModelList();
      set({ models: data.models, loading: false });
    } catch {
      set({ loading: false, error: "Failed to load models." });
    }
  },

  selectModel: (model) => set({ selected: model }),

  deleteModel: async (name) => {
    set({ loading: true, error: null });
    try {
      await api.deleteModel(name);
      const models = get().models.filter((m) => m.name !== name);
      const selected = get().selected?.name === name ? null : get().selected;
      set({ models, selected, loading: false });
    } catch {
      set({ loading: false, error: "Failed to delete model." });
    }
  },

  addModel: async (name) => {
    set({ loading: true, error: null });
    try {
      await api.addModel({ name });
      await get().fetchModels();
    } catch {
      set({ loading: false, error: "Failed to pull model." });
    }
  },
}));
