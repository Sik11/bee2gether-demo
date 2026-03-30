import { reactive, watch } from "vue";

const STORAGE_KEY = "bee2gether.settings";

function loadStoredSettings() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn("Failed to restore settings", error);
    return null;
  }
}

const initialState = {
  isDarkMode: false
}

const restoredSettings = loadStoredSettings();

export function persistSettings() {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
      isDarkMode: settings.isDarkMode,
    }));
  } catch (error) {
    console.warn("Failed to persist settings", error);
  }
}

export const settings = reactive({
  ...initialState,
  ...(restoredSettings ?? {})
})

watch(
  () => settings.isDarkMode,
  () => {
    persistSettings();
  }
)
