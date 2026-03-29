<template>
  <div class="viewport">
    <div ref="mapElement" class="map-surface"></div>
    <SearchBar custom-class="search-bar" @select="onEventClicked" />
    <MapTools custom-class="filter" />
  </div>
</template>

<script setup>
import { defineEmits, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import L from 'leaflet';
import 'leaflet.markercluster';
import { getEvents } from "../store/events.js";
import { getUserLocation } from "../store/userLocation.js";
import { auth } from "../store/auth.js";
import SearchBar from './helper/Search-bar.vue';
import { pages } from '../store/pages';
import MapTools from './helper/Map-tools.vue';

const emit = defineEmits(["eventClicked"]);
const events = getEvents();
const userLocation = getUserLocation();
const mapElement = ref(null);

const fallbackCenter = { lat: 51.3948326453863, lng: -1.3221 };
const eventIcon = L.icon({
  iconUrl: "/hive.png",
  iconSize: [42, 42],
  iconAnchor: [21, 42],
  popupAnchor: [0, -36],
});
const userIcon = L.icon({
  iconUrl: "/bee.png",
  iconSize: [44, 44],
  iconAnchor: [22, 22],
  popupAnchor: [0, -18],
});

let mapInstance = null;
let clusterLayer = null;
let userMarker = null;

function initializeMap() {
  const center = userLocation.tracking ? userLocation.location : fallbackCenter;
  mapInstance = L.map(mapElement.value, {
    zoomControl: false,
  }).setView([center.lat, center.lng], 13);

  L.control.zoom({ position: "bottomleft" }).addTo(mapInstance);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(mapInstance);

  clusterLayer = L.markerClusterGroup({
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
  });
  mapInstance.addLayer(clusterLayer);
  syncUserMarker();
  syncEventMarkers();
}

function syncEventMarkers() {
  if (!mapInstance || !clusterLayer) {
    return;
  }

  clusterLayer.clearLayers();
  for (const event of events.availableEvents) {
    if (typeof event.lat !== "number" || typeof event.long !== "number") {
      continue;
    }
    const marker = L.marker([event.lat, event.long], {
      icon: eventIcon,
      title: event.name,
    });
    marker.bindTooltip(event.name, {
      direction: "top",
      offset: [0, -24],
    });
    marker.on("click", () => onEventClicked(event));
    clusterLayer.addLayer(marker);
  }
}

function syncUserMarker() {
  if (!mapInstance) {
    return;
  }

  if (!userLocation.tracking) {
    if (userMarker) {
      mapInstance.removeLayer(userMarker);
      userMarker = null;
    }
    return;
  }

  const latLng = [userLocation.location.lat, userLocation.location.lng];
  if (!userMarker) {
    userMarker = L.marker(latLng, {
      icon: userIcon,
      title: auth.user.username,
    }).addTo(mapInstance);
  } else {
    userMarker.setLatLng(latLng);
  }
}

async function onEventClicked(event) {
  if (mapInstance) {
    mapInstance.flyTo([Number(event.lat), Number(event.long)], Math.max(mapInstance.getZoom(), 14), {
      duration: 0.4,
    });
    await new Promise((resolve) => setTimeout(resolve, 350));
  }

  pages.addLayer("event-overview");
  events.selectEvent(event);
  emit("eventClicked", event);
}

onMounted(() => {
  initializeMap();
});

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.remove();
    mapInstance = null;
  }
});

watch(
  () => events.availableEvents,
  () => {
    syncEventMarkers();
  },
  { deep: true }
);

watch(
  () => userLocation.location,
  (nextLocation) => {
    if (!mapInstance || nextLocation?.lat == null || nextLocation?.lng == null) {
      return;
    }
    const shouldCenterOnUser = !userMarker;
    syncUserMarker();
    if (shouldCenterOnUser) {
      mapInstance.setView([nextLocation.lat, nextLocation.lng], 13);
    }
  },
  { deep: true }
);
</script>

<style scoped lang="scss">
.map-surface {
  height: 100vh;
  width: 100vw;
}

.search-bar {
  position: absolute;
  top: 2rem;
  left: 5rem;
  width: calc(100vw - 6rem);
  z-index: 500;
}

.filter {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  z-index: 500;
}
</style>
