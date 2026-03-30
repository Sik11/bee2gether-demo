import { reactive } from "vue";
import { markRaw } from 'vue';
import { readQueryState, updateQueryState } from "./urlState";

const STORAGE_KEY = "bee2gether.pages";

function loadStoredSelection() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch (error) {
    console.warn("Failed to restore selected page", error);
    return null;
  }
}

function persistSelection(id) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, id);
  } catch (error) {
    console.warn("Failed to persist selected page", error);
  }
}

export const pages = reactive({
  selected: undefined,
  layers: [],
  tabs: [],
  lastAction: 'setSelected',

  /**
   * Initialise the wrapper pages
   * @param {{}} tabs 
   * @param {string} id 
   */
  init(tabs, id) {
    tabs.forEach(({component}) => markRaw(component))
    pages.tabs = tabs
    const restored = loadStoredSelection();
    const queryTab = readQueryState().tab;
    const tabIds = tabs.filter((tab) => tab.label !== undefined).map((tab) => tab.id);
    const preferredTab = tabIds.includes(queryTab) ? queryTab : restored;
    const hasRestoredTab = tabIds.includes(preferredTab);
    pages.selected = hasRestoredTab ? preferredTab : id
    updateQueryState({ tab: pages.selected })
  },

  /**
   * Set the selected page & clears all layered pages
   * @param {string} id 
   */
  setSelected(id, options = {}) {
    const { syncUrl = true } = options;
    pages.selected = id
    pages.layers = []
    pages.lastAction = 'setSelected'
    persistSelection(id)
    if (syncUrl) {
      updateQueryState({ tab: id, event: null, group: null })
    }
  },
  /**
   * 
   * @param {*} id 
   */
  addLayer(id) {
    if (!pages.layers.includes(id)) {
      pages.layers.push(id)
      pages.lastAction = 'addLayer'
    }
  },
  dropLayer() {
    pages.layers.pop()
    pages.lastAction = 'dropLayer'
  },

  // These are used by Wrapper.vue
  getLabelledTabs() {
    return pages.tabs.filter(({label}) => label !== undefined)
  },
  getZIndex(id) {
    const zindex =  [pages.selected, ...pages.layers].indexOf(id) + 1
    return zindex === 0 ? 10 : zindex
  },
  isSelected(id) {
    return id === pages.selected
  },
  isVisible(id) {
    return id === pages.selected || pages.layers.includes(id)
  },
  isLayerEmpty() {
    return pages.layers.length === 0 
  }
})
