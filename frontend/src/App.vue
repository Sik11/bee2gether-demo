<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { RouterView, useRoute, useRouter } from 'vue-router';
import { auth } from './store/auth';
import { settings } from './store/settings';
import { startTrackingLocation } from './store/userLocation';
import { preloadPersonalEventData, events, resetEventsState } from './store/events';
import { groups, updateGroups, updateUserGroups, resetGroupsState } from './store/groups';
import { refreshNotifications, resetNotificationsState } from './store/notifications';
import { pages } from './store/pages';
import { connectRealtime, disconnectRealtime } from './store/realtime';

const route = useRoute();
const router = useRouter();
const isAuthRoute = computed(() => route.name === 'auth');
const deferredBootstrapTimers = new Set();

startTrackingLocation();

function queueBootstrapTask(task, delay = 0) {
  const timer = window.setTimeout(async () => {
    deferredBootstrapTimers.delete(timer);
    await task();
  }, delay);
  deferredBootstrapTimers.add(timer);
}

function clearBootstrapTasks() {
  deferredBootstrapTimers.forEach((timer) => window.clearTimeout(timer));
  deferredBootstrapTimers.clear();
}

async function preloadPrimaryViews() {
  await Promise.allSettled([
    import('./components/YourEvents.vue'),
    import('./components/YourGroups.vue'),
    import('./components/Account.vue'),
  ]);
}

async function restoreOverlayState() {
  if (!auth.isLoggedIn || !auth.user?.userId) {
    return;
  }

  const eventId = route.query.event;
  const groupId = route.query.group;

  if (groupId) {
    await groups.selectGroupById(groupId, { openLayer: true, syncUrl: false });
  } else {
    groups.clearSelectedGroup({ syncUrl: false });
    pages.dropLayer('group-overview');
  }

  if (eventId) {
    await events.selectEventById(eventId, { openLayer: true, syncUrl: false });
  } else {
    events.clearSelectedEvent({ syncUrl: false });
    pages.dropLayer('event-overview');
  }
}

function bootstrapAuthenticatedData(userId) {
  clearBootstrapTasks();
  void preloadPrimaryViews();
  void preloadPersonalEventData(userId);

  const currentRoute = typeof route.name === 'string' ? route.name : 'map';

  if (currentRoute === 'groups') {
    void Promise.allSettled([updateUserGroups(userId), updateGroups()]);
  } else if (currentRoute === 'account') {
    void Promise.allSettled([updateUserGroups(userId), refreshNotifications()]);
    queueBootstrapTask(() => updateGroups(), 600);
  } else if (currentRoute === 'events') {
    void updateUserGroups(userId);
    queueBootstrapTask(() => refreshNotifications(), 450);
  } else {
    queueBootstrapTask(() => refreshNotifications(), 450);
    queueBootstrapTask(() => updateUserGroups(userId), 900);
    queueBootstrapTask(() => updateGroups(), 1500);
  }
}

watch(
  () => route.name,
  (name) => {
    if (typeof name === 'string' && name !== 'auth') {
      pages.syncSelected(name);
    }
  },
  { immediate: true }
);

watch(
  () => route.query,
  async () => {
    if (isAuthRoute.value || !auth.isLoggedIn) {
      return;
    }
    await restoreOverlayState();
  },
  { deep: true }
);

watch(
  () => auth.user?.userId,
  async (userId) => {
    if (!auth.isLoggedIn || !userId) {
      clearBootstrapTasks();
      disconnectRealtime({ clearSubscriptions: true });
      resetEventsState();
      resetGroupsState();
      resetNotificationsState();
      router.replace({ name: 'auth' });
      return;
    }
    if (route.name === 'auth') {
      router.replace({ name: 'map' });
    }
    bootstrapAuthenticatedData(userId);
    void connectRealtime();
    void restoreOverlayState();
  },
  { immediate: true }
);

watch(
  isAuthRoute,
  (value) => {
    if (typeof document === 'undefined') {
      return;
    }
    const root = document.documentElement;
    const app = document.getElementById('app');

    document.body.style.overflow = value ? 'auto' : 'hidden';
    document.body.style.height = value ? 'auto' : '100%';
    root.style.overflow = value ? 'auto' : 'hidden';
    root.style.height = value ? 'auto' : '100%';

    if (app) {
      app.style.overflow = value ? 'visible' : 'hidden';
      app.style.height = value ? 'auto' : '100%';
      app.style.minHeight = value ? '100dvh' : '100%';
    }
  },
  { immediate: true }
);

onMounted(async () => {
  if (auth.isLoggedIn && auth.user?.userId) {
    bootstrapAuthenticatedData(auth.user.userId);
    void connectRealtime();
  }
});

onUnmounted(() => {
  clearBootstrapTasks();
  if (typeof document !== 'undefined') {
    const root = document.documentElement;
    const app = document.getElementById('app');
    document.body.style.overflow = 'hidden';
    document.body.style.height = '100%';
    root.style.overflow = 'hidden';
    root.style.height = '100%';
    if (app) {
      app.style.overflow = 'hidden';
      app.style.height = '100%';
      app.style.minHeight = '100%';
    }
  }
  disconnectRealtime();
});
</script>

<template>
  <div :class="['viewport', { 'dark-mode': settings.isDarkMode, 'auth-route': isAuthRoute }]">
    <RouterView />
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
  height: 100%;
  margin: 0;
}

body {
  background: var(--canvas);
  color: var(--ink);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color var(--transition-base), color var(--transition-base);
  overflow: hidden;
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
  height: 100dvh;
  overflow: hidden;
}

.viewport.auth-route {
  min-height: 100dvh;
  height: auto;
  overflow-y: auto;
}

#app {
  position: relative;
  overflow: hidden;
}

.soft-panel {
  background: var(--surface);
  border: 1px solid var(--border);
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
</style>
