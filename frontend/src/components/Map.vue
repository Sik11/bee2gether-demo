<template>
  <div class="viewport">
    <div ref="mapElement" class="map-surface"></div>
    <div v-if="showMapLoading || showMapRefreshing" :class="['map-loading-indicator', { 'map-loading-indicator--floating': showMapRefreshing }]" aria-label="Loading events">
      <span class="map-loading-indicator__spinner" aria-hidden="true"></span>
    </div>
    <SearchBar custom-class="search-bar" @select="onEventClicked" />
    <MapTools custom-class="filter" />
    <div class="map-controls" aria-label="Map controls">
      <button type="button" class="map-control" aria-label="Zoom in" @click="zoomIn">+</button>
      <button type="button" class="map-control" aria-label="Zoom out" @click="zoomOut">-</button>
      <button
        type="button"
        :class="['map-control', 'map-control--icon', { disabled: !hasUsableLocation(userLocation.location) }]"
        aria-label="Go to my location"
        @click="centerOnUser({ forceZoom: true })"
      >
        <span class="map-control__bee" aria-hidden="true"></span>
      </button>
      <button
        type="button"
        :class="['map-control', 'map-control--icon', { active: isThreeDimensional }]"
        aria-label="Toggle 3D view"
        @click="toggleThreeDimensional"
      >
        3D
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import maplibregl from 'maplibre-gl';
import { getEvents } from "../store/events.js";
import { getUserLocation } from "../store/userLocation.js";
import SearchBar from './helper/Search-bar.vue';
import { pages } from '../store/pages';
import MapTools from './helper/Map-tools.vue';
import { settings } from '../store/settings';
import hiveMarkerAsset from '../assets/36611134_8_bee.svg';

const emit = defineEmits(["eventClicked"]);
const events = getEvents();
const userLocation = getUserLocation();
const mapElement = ref(null);
const showMapLoading = computed(() => events.loadingAvailableEvents && !events.hasLoadedAvailableEvents);
const showMapRefreshing = computed(() => events.loadingAvailableEvents && events.hasLoadedAvailableEvents);

const fallbackCenter = { lat: 51.3948326453863, lng: -1.3221 };
const styleUrl = "https://tiles.openfreemap.org/styles/liberty";
const eventSourceId = "bee-events";
const clusterLayerId = "bee-event-clusters";
const clusterCountLayerId = "bee-event-cluster-count";
const eventCircleLayerId = "bee-event-circles";
const eventLayerId = "bee-event-markers";
const eventIconId = "bee-hive-icon";
const baseLabelLayers = [
  "waterway_line_label",
  "water_name_point_label",
  "water_name_line_label",
  "poi_r20",
  "poi_r7",
  "poi_r1",
  "poi_transit",
  "highway-name-path",
  "highway-name-minor",
  "highway-name-major",
  "label_other",
  "label_village",
  "label_town",
  "label_state",
  "label_city",
  "label_city_capital",
  "label_country_3",
  "label_country_2",
  "label_country_1",
];
const lightBeeTheme = {
  paints: {
    background: { "background-color": "#f7f1e7" },
    park: { "fill-color": "#dde4c8" },
    park_outline: { "line-color": "#c7d0ae" },
    landuse_residential: { "fill-color": "#f2eadc" },
    landcover_wood: { "fill-color": "#d2dcc1" },
    landcover_grass: { "fill-color": "#dde6cf" },
    landcover_wetland: { "fill-color": "#d0d8c3" },
    landcover_sand: { "fill-color": "#eee2c2" },
    water: { "fill-color": "#d8e8df" },
    waterway_river: { "line-color": "#abc8bf" },
    waterway_other: { "line-color": "#bfd7cf" },
    waterway_tunnel: { "line-color": "#bfd7cf" },
    road_trunk_primary: { "line-color": "#d4aa4a" },
    road_secondary_tertiary: { "line-color": "#dfc889" },
    road_minor: { "line-color": "#eadfbb" },
    road_motorway: { "line-color": "#c99535" },
    road_link: { "line-color": "#d8bd72" },
    road_service_track: { "line-color": "#efe6ca" },
    road_path_pedestrian: { "line-color": "#d8cdb3" },
    bridge_trunk_primary: { "line-color": "#d4aa4a" },
    bridge_secondary_tertiary: { "line-color": "#dfc889" },
    bridge_street: { "line-color": "#eadfbb" },
    bridge_motorway: { "line-color": "#c99535" },
    tunnel_trunk_primary: { "line-color": "#c89e44" },
    tunnel_secondary_tertiary: { "line-color": "#d4ba79" },
    tunnel_minor: { "line-color": "#dfd2b0" },
  },
  labels: {
    "text-color": "#544a41",
    "text-halo-color": "#f7f1e7",
  },
};
const darkBeeTheme = {
  paints: {
    background: { "background-color": "#0f1419" },
    park: { "fill-color": "#1d2b22" },
    park_outline: { "line-color": "#34473b" },
    landuse_residential: { "fill-color": "#161b22" },
    landcover_wood: { "fill-color": "#223126" },
    landcover_grass: { "fill-color": "#213027" },
    landcover_wetland: { "fill-color": "#253730" },
    landcover_sand: { "fill-color": "#242116" },
    water: { "fill-color": "#18262c" },
    waterway_river: { "line-color": "#3c5b63" },
    waterway_other: { "line-color": "#345058" },
    waterway_tunnel: { "line-color": "#314b51" },
    road_trunk_primary: { "line-color": "#b88e35" },
    road_secondary_tertiary: { "line-color": "#8d7a4d" },
    road_minor: { "line-color": "#514d43" },
    road_motorway: { "line-color": "#ca9d36" },
    road_link: { "line-color": "#8f7848" },
    road_service_track: { "line-color": "#434037" },
    road_path_pedestrian: { "line-color": "#4a4a45" },
    bridge_trunk_primary: { "line-color": "#b88e35" },
    bridge_secondary_tertiary: { "line-color": "#8d7a4d" },
    bridge_street: { "line-color": "#514d43" },
    bridge_motorway: { "line-color": "#ca9d36" },
    tunnel_trunk_primary: { "line-color": "#816323" },
    tunnel_secondary_tertiary: { "line-color": "#65583b" },
    tunnel_minor: { "line-color": "#3c3934" },
  },
  labels: {
    "text-color": "#ebe5d4",
    "text-halo-color": "#0f1419",
  },
};

let mapInstance = null;
let userMarker = null;
let hasCenteredOnUser = false;
let buildingLayerSpec = null;
const isThreeDimensional = ref(false);
function createUserMarkerElement() {
  const marker = document.createElement("div");
  marker.className = "user-location-marker";
  marker.innerHTML = `
    <span class="user-location-marker__body">
      <span class="user-location-marker__pulse"></span>
      <span class="user-location-marker__ring"></span>
      <span class="user-location-marker__badge">
        <span class="user-location-marker__icon"></span>
      </span>
    </span>
  `;
  return marker;
}

function updateUserMarkerScale() {
  const markerElement = userMarker?.getElement?.();
  if (!markerElement || !mapInstance) {
    return;
  }

  const zoom = mapInstance.getZoom();
  const zoomFactor = Math.min(1, Math.max(0, (zoom - 11) / 4.5));
  const scale = 0.78 + (zoomFactor * 0.2);
  markerElement.style.setProperty("--user-location-scale", scale.toFixed(3));
}

function currentThemeConfig() {
  return settings.isDarkMode ? darkBeeTheme : lightBeeTheme;
}

function createTransparentFallbackImage() {
  const canvas = document.createElement("canvas");
  canvas.width = 2;
  canvas.height = 2;
  const context = canvas.getContext("2d");
  return context?.getImageData(0, 0, 2, 2) ?? new ImageData(2, 2);
}

function installStyleImageFallbacks() {
  if (!mapInstance) {
    return;
  }

  mapInstance.on("styleimagemissing", (event) => {
    const id = event?.id;
    if (!id || mapInstance.hasImage(id)) {
      return;
    }
    mapInstance.addImage(id, createTransparentFallbackImage(), { pixelRatio: 2 });
  });
}

function buildFeatureCollection() {
  return {
    type: "FeatureCollection",
    features: events.getFilteredAvailableEvents()
      .filter((event) => typeof event.lat === "number" && typeof event.long === "number")
      .map((event) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [Number(event.long), Number(event.lat)],
        },
        properties: {
          id: String(event.id),
          name: event.name ?? "",
        },
      })),
  };
}

function hasUsableLocation(location) {
  return Number.isFinite(location?.lat)
    && Number.isFinite(location?.lng)
    && (location.lat !== 0 || location.lng !== 0);
}

function getPreferredCenter() {
  return hasUsableLocation(userLocation.location)
    ? userLocation.location
    : fallbackCenter;
}

function safeSetPaintProperty(layerId, property, value) {
  if (mapInstance?.getLayer(layerId)) {
    mapInstance.setPaintProperty(layerId, property, value);
  }
}

function applyBeeTheme() {
  if (!mapInstance?.isStyleLoaded()) {
    return;
  }

  const theme = currentThemeConfig();
  for (const [layerId, properties] of Object.entries(theme.paints)) {
    for (const [property, value] of Object.entries(properties)) {
      safeSetPaintProperty(layerId, property, value);
    }
  }

  for (const layerId of baseLabelLayers) {
    safeSetPaintProperty(layerId, "text-color", theme.labels["text-color"]);
    safeSetPaintProperty(layerId, "text-halo-color", theme.labels["text-halo-color"]);
    safeSetPaintProperty(layerId, "text-halo-width", 1.15);
  }

  safeSetPaintProperty(clusterLayerId, "circle-color", [
    "step",
    ["get", "point_count"],
    settings.isDarkMode ? "#f2b84a" : "#e0b556",
    8,
    settings.isDarkMode ? "#f6d384" : "#edcb7f",
    20,
    settings.isDarkMode ? "#fff0c8" : "#f5dfaa",
  ]);
  safeSetPaintProperty(clusterLayerId, "circle-stroke-color", settings.isDarkMode ? "#151920" : "#fff8eb");
  safeSetPaintProperty(clusterCountLayerId, "text-color", settings.isDarkMode ? "#1a1308" : "#2a1b0a");
  safeSetPaintProperty(clusterCountLayerId, "text-halo-color", settings.isDarkMode ? "#fff4d7" : "#fff7e7");
  safeSetPaintProperty(clusterCountLayerId, "text-halo-width", 0.7);
  safeSetPaintProperty(eventCircleLayerId, "circle-color", settings.isDarkMode ? "#f4c35a" : "#d59f2f");
  safeSetPaintProperty(eventCircleLayerId, "circle-radius", [
    "case",
    ["==", ["get", "id"], String(events.selected?.id ?? "")],
    13,
    9,
  ]);
  safeSetPaintProperty(eventCircleLayerId, "circle-stroke-color", settings.isDarkMode ? "#fff7de" : "#fffef7");
  safeSetPaintProperty("bee-buildings-3d", "fill-extrusion-color", settings.isDarkMode ? "#d8d8d2" : "#efe6d4");
  safeSetPaintProperty("bee-buildings-3d", "fill-extrusion-opacity", settings.isDarkMode ? 0.92 : 0.86);
}

function ensureEventSourceAndLayers() {
  if (!mapInstance || mapInstance.getSource(eventSourceId)) {
    return;
  }

  mapInstance.addSource(eventSourceId, {
    type: "geojson",
    data: buildFeatureCollection(),
    cluster: true,
    clusterMaxZoom: 13,
    clusterRadius: 46,
    generateId: true,
  });

  mapInstance.addLayer({
    id: clusterLayerId,
    type: "circle",
    source: eventSourceId,
    filter: ["has", "point_count"],
    paint: {
      "circle-color": "#e0b556",
      "circle-radius": [
        "step",
        ["get", "point_count"],
        18,
        8,
        22,
        20,
        28,
      ],
      "circle-stroke-width": 2,
      "circle-stroke-color": "#fff8eb",
      "circle-opacity": 0.96,
    },
  });

  mapInstance.addLayer({
    id: clusterCountLayerId,
    type: "symbol",
    source: eventSourceId,
    filter: ["has", "point_count"],
    layout: {
      "text-field": ["get", "point_count_abbreviated"],
      "text-font": ["Noto Sans Regular"],
      "text-size": 12,
    },
    paint: {
      "text-color": "#2a1b0a",
      "text-halo-color": "#fff7e7",
      "text-halo-width": 0.7,
    },
  });

  mapInstance.addLayer({
    id: eventCircleLayerId,
    type: "circle",
    source: eventSourceId,
    filter: ["!", ["has", "point_count"]],
    paint: {
      "circle-radius": 9,
      "circle-color": "#d59f2f",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#fffef7",
      "circle-opacity": 0.85,
    },
  });

  mapInstance.on("click", clusterLayerId, async (event) => {
    const feature = event.features?.[0];
    const clusterId = feature?.properties?.cluster_id;
    const source = mapInstance.getSource(eventSourceId);
    if (!source || clusterId == null || typeof source.getClusterExpansionZoom !== "function") {
      return;
    }

    source.getClusterExpansionZoom(clusterId, (error, zoom) => {
      if (error || !feature.geometry || feature.geometry.type !== "Point") {
        return;
      }
      mapInstance.easeTo({
        center: feature.geometry.coordinates,
        zoom,
        duration: 450,
      });
    });
  });

  const handleEventClick = async (event) => {
    const feature = event.features?.[0];
    const eventId = feature?.properties?.id;
    const selectedEvent = events.availableEvents.find((entry) => String(entry.id) === String(eventId));
    if (selectedEvent) {
      await onEventClicked(selectedEvent);
    }
  };

  mapInstance.on("click", eventCircleLayerId, handleEventClick);
  for (const layerId of [clusterLayerId, eventCircleLayerId]) {
    mapInstance.on("mouseenter", layerId, () => {
      mapInstance.getCanvas().style.cursor = "pointer";
    });
    mapInstance.on("mouseleave", layerId, () => {
      mapInstance.getCanvas().style.cursor = "";
    });
  }
}

function ensureThreeDimensionalBuildings() {
  if (!mapInstance?.isStyleLoaded() || mapInstance.getLayer("bee-buildings-3d")) {
    return;
  }

  if (!buildingLayerSpec) {
    const candidate = mapInstance.getStyle()?.layers?.find((layer) =>
      layer.id?.includes("building")
      && layer.source
      && layer["source-layer"]
      && (layer.type === "fill" || layer.type === "fill-extrusion")
    );

    if (!candidate) {
      return;
    }

    buildingLayerSpec = {
      source: candidate.source,
      sourceLayer: candidate["source-layer"],
      filter: Array.isArray(candidate.filter) ? candidate.filter : null,
    };
  }

  const extrusionLayer = {
    id: "bee-buildings-3d",
    type: "fill-extrusion",
    source: buildingLayerSpec.source,
    "source-layer": buildingLayerSpec.sourceLayer,
    minzoom: 14,
    layout: {
      visibility: "none",
    },
    paint: {
      "fill-extrusion-color": settings.isDarkMode ? "#d8d8d2" : "#efe6d4",
      "fill-extrusion-height": [
        "coalesce",
        ["to-number", ["get", "render_height"], 8],
        ["to-number", ["get", "height"], 8],
        8,
      ],
      "fill-extrusion-base": [
        "coalesce",
        ["to-number", ["get", "render_min_height"], 0],
        ["to-number", ["get", "min_height"], 0],
        0,
      ],
      "fill-extrusion-opacity": settings.isDarkMode ? 0.92 : 0.86,
    },
  };

  if (buildingLayerSpec.filter) {
    extrusionLayer.filter = buildingLayerSpec.filter;
  }

  mapInstance.addLayer(extrusionLayer);
}

async function ensureHiveIcon() {
  if (!mapInstance || mapInstance.hasImage(eventIconId)) {
    return;
  }

  const size = 112;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Failed to create hive icon context");
  }

  context.clearRect(0, 0, size, size);

  const image = new Image();
  image.decoding = "async";
  await new Promise((resolve, reject) => {
    image.onload = () => resolve();
    image.onerror = () => reject(new Error("Failed to load hive marker asset"));
    image.src = hiveMarkerAsset;
  });
  const drawWidth = 90;
  const drawHeight = 104;
  const drawX = (size - drawWidth) / 2;
  const drawY = (size - drawHeight) / 2;
  context.drawImage(image, drawX, drawY, drawWidth, drawHeight);

  const bitmap = await createImageBitmap(canvas);
  if (!mapInstance.hasImage(eventIconId)) {
    mapInstance.addImage(eventIconId, bitmap, { pixelRatio: 2 });
  }

  if (mapInstance.getSource(eventSourceId) && !mapInstance.getLayer(eventLayerId)) {
    mapInstance.addLayer({
      id: eventLayerId,
      type: "symbol",
      source: eventSourceId,
      filter: ["!", ["has", "point_count"]],
      layout: {
        "icon-image": eventIconId,
        "icon-size": [
          "interpolate",
          ["linear"],
          ["zoom"],
          11, 0.6,
          13, 0.68,
          15, 0.78,
          17, 0.88,
        ],
        "icon-anchor": "bottom",
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
      },
    });

    mapInstance.on("click", eventLayerId, async (event) => {
      const feature = event.features?.[0];
      const eventId = feature?.properties?.id;
      const selectedEvent = events.availableEvents.find((entry) => String(entry.id) === String(eventId));
      if (selectedEvent) {
        await onEventClicked(selectedEvent);
      }
    });

    mapInstance.on("mouseenter", eventLayerId, () => {
      mapInstance.getCanvas().style.cursor = "pointer";
    });
    mapInstance.on("mouseleave", eventLayerId, () => {
      mapInstance.getCanvas().style.cursor = "";
    });
  }
}

function syncEventMarkers() {
  const data = buildFeatureCollection();
  const source = mapInstance?.getSource(eventSourceId);
  if (source && typeof source.setData === "function") {
    source.setData(data);
  }

  if (import.meta.env.DEV && typeof window !== "undefined") {
    window.__beeEventFeatures = data;
  }
}

function syncUserMarker() {
  if (!mapInstance) {
    return;
  }

  if (!userLocation.tracking || !hasUsableLocation(userLocation.location)) {
    userMarker?.remove();
    userMarker = null;
    return;
  }

  const coordinates = [userLocation.location.lng, userLocation.location.lat];
  if (!userMarker) {
    userMarker = new maplibregl.Marker({
      element: createUserMarkerElement(),
      anchor: "center",
    })
      .setLngLat(coordinates)
      .addTo(mapInstance);
  } else {
    userMarker.setLngLat(coordinates);
  }

  updateUserMarkerScale();
}

async function refreshVisibleEvents() {
  if (!mapInstance) {
    return;
  }

  await events.updateAvailableEventsForBounds(getExpandedViewportBounds(mapInstance.getBounds()));
}

function getExpandedViewportBounds(rawBounds, padFactor = 0.24) {
  if (!rawBounds) {
    return rawBounds;
  }

  const south = Number(rawBounds.getSouth?.() ?? rawBounds._sw?.lat);
  const west = Number(rawBounds.getWest?.() ?? rawBounds._sw?.lng);
  const north = Number(rawBounds.getNorth?.() ?? rawBounds._ne?.lat);
  const east = Number(rawBounds.getEast?.() ?? rawBounds._ne?.lng);

  if (![south, west, north, east].every(Number.isFinite)) {
    return rawBounds;
  }

  const latPad = (north - south) * padFactor;
  const lngPad = (east - west) * padFactor;

  return {
    bottomLeftLat: south - latPad,
    bottomLeftLong: west - lngPad,
    upperRightLat: north + latPad,
    upperRightLong: east + lngPad,
  };
}

function zoomIn() {
  mapInstance?.zoomIn({ duration: 220 });
}

function zoomOut() {
  mapInstance?.zoomOut({ duration: 220 });
}

function centerOnUser({ forceZoom = false } = {}) {
  if (!mapInstance || !hasUsableLocation(userLocation.location)) {
    return;
  }

  syncUserMarker();
  hasCenteredOnUser = true;
  const target = userMarker?.getLngLat?.() ?? {
    lng: userLocation.location.lng,
    lat: userLocation.location.lat,
  };
  mapInstance.easeTo({
    center: [target.lng, target.lat],
    zoom: forceZoom ? 15.35 : Math.max(mapInstance.getZoom(), 15.35),
    pitch: isThreeDimensional.value ? 56 : 0,
    bearing: isThreeDimensional.value ? -18 : 0,
    duration: 520,
  });
}

function toggleThreeDimensional() {
  if (!mapInstance) {
    return;
  }

  isThreeDimensional.value = !isThreeDimensional.value;
  ensureThreeDimensionalBuildings();

  if (isThreeDimensional.value) {
    mapInstance.dragRotate.enable();
    mapInstance.touchZoomRotate.enableRotation();
  } else {
    mapInstance.dragRotate.disable();
    mapInstance.touchZoomRotate.disableRotation();
  }

  if (mapInstance.getLayer("bee-buildings-3d")) {
    mapInstance.setLayoutProperty(
      "bee-buildings-3d",
      "visibility",
      isThreeDimensional.value ? "visible" : "none"
    );
  }

  mapInstance.easeTo({
    pitch: isThreeDimensional.value ? 56 : 0,
    bearing: isThreeDimensional.value ? -18 : 0,
    duration: 420,
  });
}

async function initializeMap() {
  const preferredCenter = getPreferredCenter();
  const center = [preferredCenter.lng, preferredCenter.lat];
  mapInstance = new maplibregl.Map({
    container: mapElement.value,
    style: styleUrl,
    center,
    zoom: hasUsableLocation(userLocation.location) ? 15.1 : 13,
    attributionControl: false,
  });

  installStyleImageFallbacks();
  mapInstance.dragRotate.disable();
  mapInstance.touchZoomRotate.disableRotation();

  mapInstance.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

  if (import.meta.env.DEV && typeof window !== "undefined") {
    window.__beeMap = mapInstance;
  }

  mapInstance.on("zoom", () => {
    updateUserMarkerScale();
  });

  mapInstance.on("moveend", () => {
    if (pages.selected !== "map") {
      return;
    }

    void refreshVisibleEvents();
  });

  mapInstance.on("load", async () => {
    if (import.meta.env.DEV && typeof window !== "undefined") {
      window.__beeMapLoadSteps = ["load"];
    }

    applyBeeTheme();
    if (import.meta.env.DEV && typeof window !== "undefined") {
      window.__beeMapLoadSteps.push("theme");
    }
    try {
      ensureEventSourceAndLayers();
      if (import.meta.env.DEV && typeof window !== "undefined") {
        window.__beeMapLoadSteps.push("layers");
      }
      if (isThreeDimensional.value) {
        ensureThreeDimensionalBuildings();
      }
      await ensureHiveIcon();
      if (import.meta.env.DEV && typeof window !== "undefined") {
        window.__beeMapLoadSteps.push("icons");
      }
      syncEventMarkers();
      if (import.meta.env.DEV && typeof window !== "undefined") {
        window.__beeMapLoadSteps.push("events");
      }
      syncUserMarker();
      if (import.meta.env.DEV && typeof window !== "undefined") {
        window.__beeMapLoadSteps.push("user");
      }
      await refreshVisibleEvents();
      if (import.meta.env.DEV && typeof window !== "undefined") {
        window.__beeMapLoadSteps.push("viewport-events");
      }
    } catch (error) {
      console.error("Map setup failed", error);
      if (import.meta.env.DEV && typeof window !== "undefined") {
        window.__beeMapLoadSteps.push(`setup-error:${error?.message ?? error}`);
      }
    }

  });
}

async function onEventClicked(event) {
  if (mapInstance) {
    mapInstance.flyTo({
      center: [Number(event.long), Number(event.lat)],
      zoom: Math.max(mapInstance.getZoom(), 14),
      duration: 400,
    });
    await new Promise((resolve) => setTimeout(resolve, 350));
  }

  events.selectEvent(event);
  emit("eventClicked", event);
}

onMounted(() => {
  void initializeMap();
});

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.remove();
    mapInstance = null;
  }
  userMarker = null;
});

watch(
  () => events.availableEvents,
  () => {
    syncEventMarkers();
  },
  { deep: true }
);

watch(
  () => ({ ...events.filters }),
  () => {
    syncEventMarkers();
  },
  { deep: true }
);

watch(
  () => settings.isDarkMode,
  () => {
    applyBeeTheme();
  }
);

watch(
  () => events.selected?.id,
  () => {
    applyBeeTheme();
  }
);

watch(
  () => userLocation.location,
  async (nextLocation) => {
    if (!mapInstance || nextLocation?.lat == null || nextLocation?.lng == null) {
      return;
    }

    if (!hasUsableLocation(nextLocation)) {
      return;
    }

    syncUserMarker();
    if (!hasCenteredOnUser) {
      centerOnUser({ forceZoom: true });
    }
  },
  { deep: true }
);
</script>

<style scoped lang="scss">
.viewport {
  position: relative;
  height: 100%;
  min-height: 100%;
  overflow: hidden;
  border-radius: var(--radius-lg);
  background: var(--surface-muted);
  box-shadow: var(--shadow-sm);
}

.map-surface {
  height: 100%;
  min-height: 100%;
  width: 100%;
}

:deep(.maplibregl-map),
:deep(.maplibregl-canvas-container),
:deep(.maplibregl-canvas) {
  font-family: var(--font-body);
  width: 100%;
  height: 100%;
  display: block;
}

:deep(.maplibregl-canvas) {
  border-radius: inherit;
}

:deep(.maplibregl-ctrl-attrib) {
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  border-radius: 999px 0 0 0;
  color: var(--ink-soft);
}

:deep(.maplibregl-ctrl-attrib a) {
  color: var(--secondary);
}

.search-bar {
  position: absolute;
  top: 1.1rem;
  left: 1.1rem;
  width: min(49rem, calc(100% - 2.2rem));
  z-index: 500;
}

.map-loading-indicator {
  position: absolute;
  top: 5.9rem;
  left: 1.1rem;
  z-index: 490;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.8rem;
  height: 2.8rem;
  padding: 0;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--border) 82%, transparent);
  background: color-mix(in srgb, var(--surface) 86%, transparent);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(14px);
}

.map-loading-indicator--floating {
  width: 2.6rem;
  height: 2.6rem;
}

.map-loading-indicator__spinner {
  width: 1.1rem;
  height: 1.1rem;
  flex: 0 0 1.1rem;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--accent) 26%, transparent);
  border-top-color: var(--accent);
  animation: map-loader-spin 0.8s linear infinite;
}

.filter {
  position: absolute;
  right: 1rem;
  bottom: 1rem;
  z-index: 500;
}

.map-controls {
  position: absolute;
  left: 1rem;
  bottom: 1rem;
  z-index: 520;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.map-control {
  width: 3.15rem;
  height: 3.15rem;
  display: grid;
  place-items: center;
  border-radius: 1.15rem;
  border: 1px solid var(--border);
  background: var(--map-control-surface);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
  font-size: 1.4rem;
  font-weight: 800;
  line-height: 1;
  cursor: pointer;
  transition:
    transform var(--transition-fast),
    background-color var(--transition-fast),
    color var(--transition-fast),
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.map-control:hover {
  transform: translateY(-1px);
  background: var(--chrome-hover);
  color: var(--ink);
  border-color: var(--border-strong);
}

.map-control--icon {
  font-size: 0.95rem;
  letter-spacing: 0.02em;
}

.map-control__emoji {
  font-size: 1.2rem;
  line-height: 1;
}

.map-control__bee {
  width: 1.35rem;
  height: 1.35rem;
  display: block;
  background: center / contain no-repeat url("/bee.png");
}

.map-control.active {
  background: var(--accent);
  color: var(--accent-ink);
  border-color: color-mix(in srgb, var(--accent-strong) 70%, var(--border));
}

.map-control.disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .map-surface {
    height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 2rem);
    min-height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 2rem);
  }
}

@media (max-width: 768px) {
  .search-bar {
    width: calc(100% - 5.4rem);
    left: 1rem;
    top: 1rem;
  }

  .map-loading-indicator {
    top: 5.5rem;
    left: 1rem;
    max-width: calc(100% - 2rem);
    min-width: 0;
  }

  .map-controls {
    left: 0.8rem;
    bottom: calc(var(--bottom-nav-height) + 1.1rem);
  }
}

:deep(.user-location-marker) {
  position: relative;
  width: 3.35rem;
  height: 3.35rem;
}

:deep(.user-location-marker__body) {
  position: absolute;
  inset: 0;
  transform-origin: center;
  transform: scale(var(--user-location-scale, 0.92));
}

:deep(.user-location-marker__pulse),
:deep(.user-location-marker__ring),
:deep(.user-location-marker__badge),
:deep(.user-location-marker__icon) {
  position: absolute;
}

:deep(.user-location-marker__pulse) {
  inset: 0.15rem;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 26%, transparent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 26%, transparent);
  transform: scale(0.88);
  animation: bee-pulse 2.2s ease-in-out infinite;
}

:deep(.user-location-marker__ring) {
  inset: 0.4rem;
  border-radius: 50%;
  background: color-mix(in srgb, var(--surface) 92%, white 8%);
  border: 2px solid color-mix(in srgb, var(--accent-strong) 68%, white 32%);
  box-shadow:
    0 12px 24px rgba(0, 0, 0, 0.22),
    0 0 0 4px color-mix(in srgb, var(--accent) 18%, transparent);
}

:deep(.user-location-marker__badge) {
  inset: 0.68rem;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.95), rgba(255, 248, 230, 0.82) 45%, rgba(255, 235, 182, 0.6) 100%),
    color-mix(in srgb, var(--surface) 84%, white 16%);
}

:deep(.user-location-marker__icon) {
  inset: 0.34rem;
  background: center / contain no-repeat url("/bee.png");
  filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.18));
}

@keyframes bee-pulse {
  0%,
  100% {
    opacity: 0.4;
    transform: scale(0.88);
  }

  50% {
    opacity: 0.75;
    transform: scale(1.08);
  }
}

@keyframes map-loader-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
