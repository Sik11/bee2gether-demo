import { reactive } from "vue";

const STORAGE_KEY = "bee2gether.route";

function persistRouteSelection(routeName) {
  if (typeof window === "undefined" || !routeName) {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, routeName);
  } catch (error) {
    console.warn("Failed to persist selected route", error);
  }
}

function loadRouteSelection() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch (error) {
    console.warn("Failed to restore selected route", error);
    return null;
  }
}

export const navItems = [
  { id: "map", text: "Map", iconKey: "map", to: "/map" },
  { id: "events", text: "Your Events", iconKey: "calendar", to: "/events" },
  { id: "groups", text: "Groups", iconKey: "groups", to: "/groups" },
  { id: "account", text: "Account", iconKey: "account", to: "/account" },
];

export const pages = reactive({
  selected: loadRouteSelection() || "map",
  layers: [],

  syncSelected(id) {
    pages.selected = id;
    persistRouteSelection(id);
  },

  addLayer(id) {
    if (!pages.layers.includes(id)) {
      pages.layers.push(id);
    }
  },

  dropLayer(id) {
    if (!id) {
      pages.layers.pop();
      return;
    }
    pages.layers = pages.layers.filter((layerId) => layerId !== id);
  },

  clearLayers() {
    pages.layers = [];
  },

  isLayerVisible(id) {
    return pages.layers.includes(id);
  },
});
