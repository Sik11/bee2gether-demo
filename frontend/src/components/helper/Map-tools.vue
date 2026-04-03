<script setup>
import { computed, ref } from 'vue';
import { mdiPlus, mdiCrosshairsGps } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { pages } from '../../store/pages';
import { userLocation } from '../../store/userLocation';
import { getEvents } from '../../store/events';

const { customClass } = defineProps({
  customClass: { type: [String, Object, Array], default: "" },
});

const isRefreshing = ref(false);

const canRefreshNearby = computed(() =>
  Boolean(getEvents().viewportBounds)
  || (
    Number.isFinite(userLocation.location?.lat)
    && Number.isFinite(userLocation.location?.lng)
    && (userLocation.location.lat !== 0 || userLocation.location.lng !== 0)
  )
);

async function refreshNearby() {
  if (!canRefreshNearby.value || isRefreshing.value) {
    return;
  }

  isRefreshing.value = true;
  const startedAt = Date.now();
  try {
    if (getEvents().viewportBounds) {
      await getEvents().updateAvailableEventsForBounds(getEvents().viewportBounds);
    } else {
      await getEvents().updateAvailableEvents(userLocation.location.lat, userLocation.location.lng);
    }
  } finally {
    const visibleDuration = Date.now() - startedAt;
    const remainingDelay = Math.max(0, 650 - visibleDuration);
    window.setTimeout(() => {
      isRefreshing.value = false;
    }, remainingDelay);
  }
}
</script>

<template>
  <div :class="['map-tools', customClass]">
    <button type="button" class="tool tool-primary" @click="() => pages.addLayer('create-event')">
      <svg-icon :path="mdiPlus" height="1.15rem"/>
      <span>Create Event</span>
    </button>
    <button
      type="button"
      class="tool"
      :disabled="!canRefreshNearby || isRefreshing"
      @click="refreshNearby"
    >
      <svg-icon :path="mdiCrosshairsGps" height="1rem"/>
      <span>{{ isRefreshing ? 'Refreshing...' : 'Refresh Nearby' }}</span>
    </button>
  </div>
</template>

<style scoped lang="scss">
.map-tools {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.75rem;
}

.tool {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  min-height: 3rem;
  padding: 0.8rem 1rem;
  border-radius: var(--radius-pill);
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--ink);
  font-weight: 700;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast);
}

.tool:hover:not(:disabled) {
  transform: translateY(-1px);
  background: var(--chrome-hover);
}

.tool:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tool-primary {
  background: var(--accent);
  color: #20160d;
}

.tool-primary:hover:not(:disabled) {
  background: var(--accent-strong);
}

@media (max-width: 768px) {
  .tool span {
    display: none;
  }

  .tool {
    width: 3.35rem;
    height: 3.35rem;
    padding: 0;
  }
}
</style>
