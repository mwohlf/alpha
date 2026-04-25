import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { api } from "../api";
import type { OllamaModel } from "../generated/models";
import { useChatStore } from "./useChatStore";

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

export const useModelsStore = create<ModelsState>()(
  devtools(
    (set, get) => ({
      models: [],
      selected: null,
      loading: false,
      error: null,

      fetchModels: async () => {
        set({ loading: true, error: null, selected: null });
        try {
          const { data } = await api.getModelList();
          const models = data.models ?? [];
          const { selectedModel, setSelectedModel } = useChatStore.getState();
          const match =
            (selectedModel && models.find((m) => m.name === selectedModel)) ||
            models[0];
          if (match && !selectedModel) setSelectedModel(match.name);
          set({ models, selected: match ?? null, loading: false });
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
          const selected =
            get().selected?.name === name ? null : get().selected;
          set({ models, selected, loading: false });
        } catch {
          set({ loading: false, error: "Failed to delete model." });
        }
      },

      addModel: async (name) => {
        set({ loading: true, error: null });
        try {
          await api.addModel({ name });
        } catch {
          set({ loading: false, error: "Failed to pull model." });
          return;
        }
        await get().fetchModels();
      },
    }),
    { name: "ModelsStore" },
  ),
);
