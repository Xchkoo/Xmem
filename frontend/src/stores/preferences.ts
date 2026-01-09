import { defineStore } from "pinia";

export type NoteCopyFormat = "plain" | "raw";

type PreferencesState = {
  quickDeleteEnabled: boolean;
  noteCopyFormat: NoteCopyFormat;
};

const STORAGE_KEY = "preferences";
let subscriptionAttached = false;

const readJson = (value: string | null): unknown => {
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null && !Array.isArray(value);
};

const coerceNoteCopyFormat = (value: unknown): NoteCopyFormat | null => {
  if (value === "plain" || value === "raw") return value;
  return null;
};

const loadPreferencesFromStorage = (): Partial<PreferencesState> => {
  if (typeof window === "undefined") return {};

  const raw = localStorage.getItem(STORAGE_KEY);
  const parsed = readJson(raw);
  const result: Partial<PreferencesState> = {};

  if (isRecord(parsed)) {
    if (typeof parsed.quickDeleteEnabled === "boolean") {
      result.quickDeleteEnabled = parsed.quickDeleteEnabled;
    }
    const format = coerceNoteCopyFormat(parsed.noteCopyFormat);
    if (format) {
      result.noteCopyFormat = format;
    }
  }

  return result;
};

const persistPreferencesToStorage = (state: PreferencesState) => {
  if (typeof window === "undefined") return;
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      quickDeleteEnabled: state.quickDeleteEnabled,
      noteCopyFormat: state.noteCopyFormat,
    }),
  );
};

export const usePreferencesStore = defineStore("preferences", {
  state: (): PreferencesState => ({
    quickDeleteEnabled: false,
    noteCopyFormat: "raw",
  }),
  actions: {
    init() {
      const loaded = loadPreferencesFromStorage();
      if (typeof loaded.quickDeleteEnabled === "boolean") {
        this.quickDeleteEnabled = loaded.quickDeleteEnabled;
      }
      if (loaded.noteCopyFormat) {
        this.noteCopyFormat = loaded.noteCopyFormat;
      }

      if (!subscriptionAttached) {
        subscriptionAttached = true;
        this.$subscribe((_mutation, state) => {
          persistPreferencesToStorage(state);
        });
      }
    },
    setQuickDeleteEnabled(enabled: boolean) {
      this.quickDeleteEnabled = enabled;
    },
    setNoteCopyFormat(format: NoteCopyFormat) {
      this.noteCopyFormat = format;
    },
  },
});
