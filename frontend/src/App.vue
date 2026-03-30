<script setup>
import { computed, defineAsyncComponent, onMounted, watch } from 'vue';
import { mdiMap, mdiCalendar, mdiAccountCircle, mdiAccountGroup } from '@mdi/js';
import Wrapper from "./components/helper/Wrapper.vue";
import { auth } from './store/auth';
import { pages } from './store/pages';
import { settings } from './store/settings';
import { startTrackingLocation } from './store/userLocation';
import { startPollingEvents, startPollingEventAttendees, events, updateSavedEvents } from './store/events';
import { groups, startPollingAllGroups, startPollingUserGroups } from './store/groups';
import { readQueryState } from './store/urlState';

const Auth = defineAsyncComponent(() => import('./components/Auth.vue'));
const Map = defineAsyncComponent(() => import('./components/Map.vue'));
const CreateEvent = defineAsyncComponent(() => import('./components/CreateEvent.vue'));
const YourEvents = defineAsyncComponent(() => import('./components/YourEvents.vue'));
const YourGroups = defineAsyncComponent(() => import('./components/YourGroups.vue'));
const CreateGroups = defineAsyncComponent(() => import('./components/CreateGroup.vue'));
const GroupOverview = defineAsyncComponent(() => import('./components/GroupOverview.vue'));
const Account = defineAsyncComponent(() => import('./components/Account.vue'));
const EventOverview = defineAsyncComponent(() => import('./components/EventOverview.vue'));

startTrackingLocation();
startPollingEvents();
startPollingAllGroups();
startPollingUserGroups();
startPollingEventAttendees();

pages.init([
  { component: Map, id: "map", label: { text: "Map", icon: mdiMap }, props: { unsued: 'this feature does exist' } },
  { component: YourEvents, id: "events", label: { text: "Your Events", icon: mdiCalendar } },
  { component: YourGroups, id: "groups", label: { text: "Groups", icon: mdiAccountGroup } },
  { component: Account, id: "account", label: { text: "Account", icon: mdiAccountCircle } },
  { component: CreateEvent, id: "create-event" },
  { component: CreateGroups, id: "create-group" },
  { component: GroupOverview, id: "group-overview" },
  { component: EventOverview, id: "event-overview" }
], 'map');

const initialBootResolved = computed(() => auth.isLoggedIn && Boolean(auth.user?.userId));

async function restoreDeepLinkState() {
  if (!initialBootResolved.value) {
    return;
  }

  const query = readQueryState();
  if (query.event) {
    await events.selectEventById(query.event, { openLayer: true, syncUrl: false });
    return;
  }
  if (query.group) {
    await groups.selectGroupById(query.group, { openLayer: true, syncUrl: false });
  }
}

watch(
  () => auth.user?.userId,
  async (userId) => {
    if (!auth.isLoggedIn || !userId) {
      return;
    }
    await updateSavedEvents(userId);
    await restoreDeepLinkState();
  },
  { immediate: true }
);

onMounted(async () => {
  if (auth.isLoggedIn && auth.user?.userId) {
    await updateSavedEvents(auth.user.userId);
    await restoreDeepLinkState();
  }
});
</script>

<template>
  <div :class="['viewport', { 'dark-mode': settings.isDarkMode }]">
    <Auth v-if="!auth.isLoggedIn" />
    <Wrapper v-else />
  </div>
</template>

<style>
@import './assets/themes.css';

*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
  margin: 0;
}

body {
  background:
    radial-gradient(circle at top left, rgba(244, 178, 35, 0.1), transparent 28%),
    radial-gradient(circle at bottom right, rgba(44, 122, 123, 0.08), transparent 30%),
    var(--canvas);
  color: var(--ink);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color var(--transition-base), color var(--transition-base);
}

a,
button,
input,
textarea,
select {
  font: inherit;
}

button {
  border: 0;
}

button:focus {
  outline: none;
}

img {
  max-width: 100%;
  display: block;
}

.viewport {
  width: 100%;
  min-height: 100dvh;
}

#app {
  position: relative;
}

.soft-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(12px);
}

.field,
.textarea,
.select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  color: var(--ink);
  padding: 0.95rem 1rem;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast);
}

.field::placeholder,
.textarea::placeholder {
  color: var(--ink-muted);
}

.field:focus,
.textarea:focus,
.select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  min-height: 3rem;
  padding: 0.85rem 1.2rem;
  border-radius: var(--radius-pill);
  font-weight: 700;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition: transform var(--transition-fast), background-color var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast);
}

.btn:hover {
  transform: translateY(-1px);
  color: inherit;
}

.btn-primary {
  background: var(--accent);
  color: var(--accent-ink);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: var(--accent-strong);
  color: var(--accent-ink);
}

.btn:focus-visible,
.theme-btn:focus-visible,
.tool:focus-visible,
.map-control:focus-visible,
.nav-item:focus-visible,
.bottom-nav__item:focus-visible,
.tab-btn:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent),
    0 0 0 1px color-mix(in srgb, var(--accent-strong) 72%, var(--border));
}

.btn-secondary {
  background: var(--surface-strong);
  color: var(--ink);
  border: 1px solid var(--border);
}

.btn-secondary:hover {
  background: var(--chrome-hover);
  color: var(--ink);
}

.btn-ghost {
  background: transparent;
  color: var(--ink-soft);
}

.btn-ghost:hover {
  background: var(--chrome-hover);
  color: var(--ink);
}

.btn-danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.btn-danger:hover {
  background: rgba(198, 79, 52, 0.2);
  color: var(--danger);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.8rem;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.section-title {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: -0.03em;
}

.section-copy {
  color: var(--ink-soft);
  line-height: 1.6;
}
</style>
