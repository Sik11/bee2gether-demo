<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import maplibregl from 'maplibre-gl';
import { mdiCrosshairsGps, mdiMapMarker, mdiMinus, mdiPlus } from '@mdi/js';
import svgIcon from './svg-icon.vue';

const props = defineProps({
  coordinates: {
    type: Object,
    default: () => ({ lat: null, lng: null }),
  },
  userCoordinates: {
    type: Object,
    default: () => ({ lat: null, lng: null }),
  },
  fallbackCenter: {
    type: Object,
    default: () => ({ lat: 51.3948326453863, lng: -1.3221 }),
  },
  summaryTitle: {
    type: String,
    default: 'Selected location',
  },
  summarySubtitle: {
    type: String,
    default: '',
  },
  interactive: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['selectCoordinates']);

const styleUrl = 'https://tiles.openfreemap.org/styles/liberty';
const mapElement = ref(null);
let mapInstance = null;
let marker = null;

const hasCoordinates = computed(() =>
  Number.isFinite(props.coordinates?.lat) &&
  Number.isFinite(props.coordinates?.lng) &&
  (props.coordinates.lat !== 0 || props.coordinates.lng !== 0)
);

const hasUserCoordinates = computed(() =>
  Number.isFinite(props.userCoordinates?.lat) &&
  Number.isFinite(props.userCoordinates?.lng) &&
  (props.userCoordinates.lat !== 0 || props.userCoordinates.lng !== 0)
);

function currentCenter() {
  if (hasCoordinates.value) {
    return [props.coordinates.lng, props.coordinates.lat];
  }
  if (hasUserCoordinates.value) {
    return [props.userCoordinates.lng, props.userCoordinates.lat];
  }
  return [props.fallbackCenter.lng, props.fallbackCenter.lat];
}

function currentZoom() {
  if (hasCoordinates.value) {
    return 15.2;
  }
  if (hasUserCoordinates.value) {
    return 13.6;
  }
  return 12.4;
}

function syncMarker({ animate = false } = {}) {
  if (!mapInstance) {
    return;
  }

  if (!hasCoordinates.value) {
    marker?.remove();
    marker = null;
    return;
  }

  const lngLat = [props.coordinates.lng, props.coordinates.lat];
  if (!marker) {
    const markerNode = document.createElement('div');
    markerNode.className = 'event-sheet-map-marker';
    markerNode.innerHTML = '<span class="event-sheet-map-marker__pin"></span>';
    marker = new maplibregl.Marker({
      element: markerNode,
      anchor: 'bottom',
    }).setLngLat(lngLat).addTo(mapInstance);
  } else {
    marker.setLngLat(lngLat);
  }

  if (animate) {
    mapInstance.easeTo({
      center: lngLat,
      zoom: Math.max(mapInstance.getZoom(), 15),
      duration: 450,
    });
  }
}

function initializeMap() {
  if (!mapElement.value || mapInstance) {
    return;
  }

  mapInstance = new maplibregl.Map({
    container: mapElement.value,
    style: styleUrl,
    center: currentCenter(),
    zoom: currentZoom(),
    attributionControl: false,
    dragRotate: false,
    pitchWithRotate: false,
    cooperativeGestures: false,
    interactive: true,
  });

  mapInstance.on('load', () => {
    syncMarker();
  });

  if (props.interactive) {
    mapInstance.on('click', (event) => {
      emit('selectCoordinates', {
        lat: Number(event.lngLat.lat),
        lng: Number(event.lngLat.lng),
      });
    });
  }
}

function zoomIn() {
  mapInstance?.easeTo({ zoom: Math.min((mapInstance.getZoom() || 0) + 1, 18), duration: 220 });
}

function zoomOut() {
  mapInstance?.easeTo({ zoom: Math.max((mapInstance.getZoom() || 0) - 1, 3), duration: 220 });
}

function centerOnUser() {
  if (!mapInstance || !hasUserCoordinates.value) {
    return;
  }
  mapInstance.easeTo({
    center: [props.userCoordinates.lng, props.userCoordinates.lat],
    zoom: 15,
    duration: 350,
  });
}

watch(
  () => [props.coordinates?.lat, props.coordinates?.lng],
  () => {
    if (!mapInstance) {
      return;
    }
    syncMarker({ animate: true });
  }
);

watch(
  () => [props.userCoordinates?.lat, props.userCoordinates?.lng],
  () => {
    if (!mapInstance || hasCoordinates.value) {
      return;
    }
    mapInstance.easeTo({ center: currentCenter(), zoom: currentZoom(), duration: 350 });
  }
);

onMounted(initializeMap);

onBeforeUnmount(() => {
  marker?.remove();
  marker = null;
  mapInstance?.remove();
  mapInstance = null;
});
</script>

<template>
  <section class="event-map-pane">
    <div v-if="$slots.toolbar" class="event-map-pane__toolbar">
      <slot name="toolbar" />
    </div>

    <div class="event-map-pane__surface">
      <div ref="mapElement" class="event-map-pane__canvas"></div>

      <div class="event-map-pane__controls" aria-label="Event sheet map controls">
        <button type="button" class="event-map-pane__control" aria-label="Zoom in" @click="zoomIn">
          <svg-icon :path="mdiPlus" width="1rem" height="1rem" />
        </button>
        <button type="button" class="event-map-pane__control" aria-label="Zoom out" @click="zoomOut">
          <svg-icon :path="mdiMinus" width="1rem" height="1rem" />
        </button>
        <button
          type="button"
          class="event-map-pane__control event-map-pane__control--bee"
          :disabled="!hasUserCoordinates"
          aria-label="Center on my location"
          @click="centerOnUser"
        >
          <svg-icon :path="mdiCrosshairsGps" width="1rem" height="1rem" />
        </button>
      </div>

      <div class="event-map-pane__summary">
        <div class="event-map-pane__summary-icon">
          <svg-icon :path="mdiMapMarker" width="1rem" height="1rem" />
        </div>
        <div class="event-map-pane__summary-copy">
          <strong>{{ summaryTitle }}</strong>
          <span>{{ summarySubtitle }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
.event-map-pane {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  height: 100%;
  min-height: 0;
}

.event-map-pane__toolbar {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.event-map-pane__surface {
  position: relative;
  flex: 1;
  min-height: 23rem;
  overflow: hidden;
  border-radius: 1.6rem;
  border: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
  background: color-mix(in srgb, var(--canvas-strong) 70%, var(--surface));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.event-map-pane__canvas {
  position: absolute;
  inset: 0;
}

.event-map-pane__controls {
  position: absolute;
  right: 0.95rem;
  bottom: 1.1rem;
  display: grid;
  gap: 0.55rem;
  z-index: 2;
}

.event-map-pane__control {
  width: 2.65rem;
  height: 2.65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  color: var(--ink);
  box-shadow: 0 8px 20px rgba(20, 15, 10, 0.12);
  transition: transform var(--transition-fast), background-color var(--transition-fast);
}

.event-map-pane__control:hover:not(:disabled) {
  transform: translateY(-1px);
  background: color-mix(in srgb, var(--surface) 98%, transparent);
}

.event-map-pane__control:disabled {
  opacity: 0.45;
  cursor: default;
}

.event-map-pane__control--bee {
  color: var(--accent-ink);
  background: color-mix(in srgb, var(--accent) 88%, white);
}

.event-map-pane__summary {
  position: absolute;
  left: 0.95rem;
  right: 4.85rem;
  bottom: 1rem;
  z-index: 2;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.75rem;
  align-items: center;
  padding: 0.8rem 0.9rem;
  border-radius: 1.1rem;
  background: color-mix(in srgb, var(--surface) 95%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 86%, transparent);
  box-shadow: 0 18px 32px rgba(20, 15, 10, 0.12);
}

.event-map-pane__summary-icon {
  width: 2.1rem;
  height: 2.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 22%, transparent);
  color: var(--accent-strong);
}

.event-map-pane__summary-copy {
  display: grid;
  gap: 0.15rem;
  min-width: 0;

  strong,
  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  strong {
    font-size: 0.98rem;
    color: var(--ink);
  }

  span {
    font-size: 0.88rem;
    color: var(--ink-muted);
  }
}

:deep(.event-sheet-map-marker) {
  width: 1.65rem;
  height: 1.65rem;
}

:deep(.event-sheet-map-marker__pin) {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 999px 999px 999px 0;
  transform: rotate(-45deg);
  background: linear-gradient(145deg, color-mix(in srgb, var(--accent) 90%, white), var(--accent));
  border: 2px solid color-mix(in srgb, white 82%, transparent);
  box-shadow: 0 10px 18px rgba(212, 162, 42, 0.26);
}

@media (max-width: 860px) {
  .event-map-pane__surface {
    min-height: 18rem;
  }
}
</style>
