import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { api } from "../api";

interface DatabaseState {
  wiping: boolean;
  error: string | null;
  lastWipe: Record<string, number> | null;
  wipe: () => Promise<void>;
}

export const useDatabaseStore = create<DatabaseState>()(
  devtools(
    (set) => ({
      wiping: false,
      error: null,
      lastWipe: null,

      wipe: async () => {
        set({ wiping: true, error: null, lastWipe: null });
        try {
          const { data } = await api.wipeDatabase();
          set({ wiping: false, lastWipe: data.deleted });
        } catch {
          set({ wiping: false, error: "Failed to wipe database" });
        }
      },
    }),
    { name: "DatabaseStore" },
  ),
);
