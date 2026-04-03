<script setup>
import { computed } from 'vue';
import { RouterView, useRoute, useRouter } from 'vue-router';
import { mdiAccountCircle, mdiBellOutline, mdiCalendar, mdiMap, mdiPlus, mdiThemeLightDark, mdiAccountGroup } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { auth } from '../../store/auth';
import { navItems, pages } from '../../store/pages';
import { notifications } from '../../store/notifications';
import { settings } from '../../store/settings';
import { updateQueryState } from '../../store/urlState';
import logo from '../../assets/logo.png';
import darkLogo from '../../assets/dark-logo.png';
import CreateEvent from '../CreateEvent.vue';
import CreateGroup from '../CreateGroup.vue';
import GroupOverview from '../GroupOverview.vue';
import EventOverview from '../EventOverview.vue';
import NotificationsPanel from '../NotificationsPanel.vue';

const route = useRoute();
const router = useRouter();

const iconMap = {
  map: mdiMap,
  calendar: mdiCalendar,
  groups: mdiAccountGroup,
  account: mdiAccountCircle,
};

const topbarCreateHiddenPages = ["map", "events", "account"];
const showTopbarCreateAction = computed(() => !topbarCreateHiddenPages.includes(String(route.name)));
const notificationsOpen = computed(() => route.query.notifications === '1');
const overlayActive = computed(() => pages.layers.length > 0 || notificationsOpen.value);

const overlayComponents = {
  'create-event': CreateEvent,
  'create-group': CreateGroup,
  'group-overview': GroupOverview,
  'event-overview': EventOverview,
};

const toggleTheme = () => {
  settings.isDarkMode = !settings.isDarkMode;
};

const select = (id) => {
  const item = navItems.find((entry) => entry.id === id);
  if (!item) {
    return;
  }
  pages.clearLayers();
  router.push(item.to);
};

function toggleNotifications() {
  updateQueryState({ notifications: notificationsOpen.value ? null : 1 });
}
</script>

<template>
  <div :class="['app-shell', { 'overlay-active': overlayActive }]">
    <header class="topbar">
      <div class="brand-block">
        <img :src="settings.isDarkMode ? darkLogo : logo" alt="Bee2Gether logo" />
        <div>
          <p class="brand-kicker">Bee2Gether</p>
          <h1>Hello, {{ auth.user.username }}</h1>
        </div>
      </div>
      <div class="topbar-actions">
        <button
          type="button"
          class="theme-btn"
          aria-label="Open notifications"
          @click="toggleNotifications"
        >
          <svg-icon :path="mdiBellOutline" height="1.15rem"/>
          <span v-if="notifications.unreadCount" class="notification-badge">{{ notifications.unreadCount }}</span>
        </button>
        <button
          v-if="showTopbarCreateAction"
          type="button"
          class="btn btn-primary action-btn"
          @click="pages.addLayer('create-event')"
        >
          <svg-icon :path="mdiPlus" height="1.1rem"/>
          <span>Create Event</span>
        </button>
        <button type="button" class="theme-btn" @click="toggleTheme" aria-label="Toggle theme">
          <svg-icon :path="mdiThemeLightDark" height="1.2rem"/>
        </button>
      </div>
    </header>

    <div class="shell-body">
      <aside class="sidebar soft-panel">
        <div class="sidebar-spacer" aria-hidden="true"></div>
        <nav class="sidebar-nav">
          <button
            v-for="item in navItems"
            :key="item.id"
            type="button"
            :class="['nav-item', { active: route.name === item.id }]"
            @click="select(item.id)"
          >
            <svg-icon :path="iconMap[item.iconKey]" height="1.15rem"/>
            <span>{{ item.text }}</span>
          </button>
        </nav>
      </aside>

      <main class="workspace">
        <RouterView />
      </main>
    </div>

    <div class="overlay-stack">
      <div
        v-for="layer in pages.layers"
        :key="layer"
        class="overlay-card"
      >
        <component :is="overlayComponents[layer]" />
      </div>
      <NotificationsPanel v-if="notificationsOpen" />
    </div>

    <nav class="bottom-nav soft-panel">
      <button
        v-for="item in navItems"
        :key="item.id"
        type="button"
        :class="['bottom-nav__item', { active: route.name === item.id }]"
        @click="select(item.id)"
      >
        <svg-icon :path="iconMap[item.iconKey]" height="1.25rem"/>
        <span>{{ item.text }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped lang="scss">
.app-shell {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  padding-bottom: 0;
  background: var(--canvas);
  color: var(--ink);
  transition: background-color var(--transition-base), color var(--transition-base);
  overflow: hidden;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1rem 0.5rem;
  background: var(--topbar-surface);
  backdrop-filter: blur(12px);
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 0.9rem;

  img {
    width: 3rem;
    height: 3rem;
  }

  p,
  h1 {
    margin: 0;
  }
}

.brand-kicker {
  color: var(--ink-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.brand-block h1 {
  font-family: var(--font-display);
  font-size: clamp(1.05rem, 2vw, 1.35rem);
  letter-spacing: -0.04em;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.action-btn {
  min-height: 2.8rem;
  padding-inline: 1rem;
}

.action-btn :deep(svg),
.theme-btn :deep(svg) {
  color: var(--action-icon);
}

.action-btn.btn-primary :deep(svg) {
  color: var(--accent-ink);
}

.theme-btn {
  width: 2.9rem;
  height: 2.9rem;
  border-radius: 50%;
  background: var(--chrome-surface);
  border: 1px solid var(--border);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
}

.theme-btn:hover {
  background: var(--chrome-hover);
  color: var(--ink);
  transform: translateY(-1px);
}

.shell-body {
  --shell-panel-height: calc(100dvh - var(--topbar-height));
  flex: 1;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  gap: 1rem;
  padding: 0 1rem 0;
  align-items: start;
  min-height: calc(100dvh - var(--topbar-height));
  max-height: calc(100dvh - var(--topbar-height));
  overflow: hidden;
  isolation: isolate;
}

.sidebar {
  position: sticky;
  z-index: 6;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  border-radius: var(--radius-lg);
  background: var(--chrome-surface);
  top: calc(var(--topbar-height) + 0.5rem);
  height: var(--shell-panel-height);
  min-height: var(--shell-panel-height);
  max-height: var(--shell-panel-height);
  overflow: auto;
  align-self: start;
  margin-bottom: 1rem;
  height: calc(var(--shell-panel-height) - 1rem);
  min-height: calc(var(--shell-panel-height) - 1rem);
  max-height: calc(var(--shell-panel-height) - 1rem);
}

.sidebar-spacer {
  min-height: 2.85rem;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  position: relative;
  z-index: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.95rem 1rem;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--ink-soft);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);

  &:hover,
  &.active {
    background: var(--chrome-hover);
    color: var(--ink);
    transform: translateX(2px);
  }
}

.nav-item :deep(svg) {
  color: var(--nav-icon);
}

.nav-item:hover :deep(svg),
.nav-item.active :deep(svg) {
  color: var(--nav-icon-active);
}

.workspace {
  position: relative;
  z-index: 1;
  min-width: 0;
  height: calc(var(--shell-panel-height) - 1rem);
  max-height: calc(var(--shell-panel-height) - 1rem);
  overflow: auto;
  overscroll-behavior: contain;
  background: transparent;
  transition: background-color var(--transition-base);
  margin-bottom: 1rem;
}

.notification-badge {
  position: absolute;
  top: 0.55rem;
  right: 0.55rem;
  width: 0.52rem;
  height: 0.52rem;
  border-radius: 999px;
  background: #5da7ff;
  box-shadow: 0 0 0 3px color-mix(in srgb, #5da7ff 18%, transparent);
}

.overlay-stack {
  position: fixed;
  inset: var(--topbar-height) 0 0 0;
  z-index: 70;
  pointer-events: none;
}

.overlay-card {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow: auto;
  padding: 0.75rem 1rem 0.8rem;
  pointer-events: auto;
  background:
    radial-gradient(circle at top center, color-mix(in srgb, var(--surface) 8%, transparent), transparent 24rem),
    color-mix(in srgb, var(--canvas) 76%, transparent);
  backdrop-filter: saturate(0.78) blur(7px);
}

.overlay-card :deep(.page-wrapper) {
  width: min(100%, 46rem);
  max-height: calc(100dvh - var(--topbar-height) - 2.3rem);
  min-height: 0;
  padding: 0;
  gap: 0.75rem;
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable both-edges;
  border-radius: calc(var(--radius-lg) + 0.1rem);
  border: 1px solid color-mix(in srgb, var(--border-strong) 88%, transparent);
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  box-shadow:
    0 24px 60px rgba(18, 16, 12, 0.18),
    0 1px 0 rgba(255, 255, 255, 0.35) inset;
}

.overlay-card :deep(.event-sheet) {
  margin-top: 0;
  position: relative;
  z-index: 1;
}

.app-shell.overlay-active .workspace :deep(.search-bar),
.app-shell.overlay-active .workspace :deep(.filter),
.app-shell.overlay-active .workspace :deep(.map-controls) {
  opacity: 0;
  pointer-events: none;
  transform: scale(0.96);
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast);
}

.overlay-card :deep(.page-title) {
  display: none;
}

.bottom-nav {
  position: fixed;
  left: 50%;
  bottom: 0.75rem;
  transform: translateX(-50%);
  z-index: 30;
  width: min(calc(100% - 1.5rem), 28rem);
  display: none;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  padding: 0.55rem;
  border-radius: calc(var(--radius-lg) + 0.2rem);
}

.bottom-nav__item {
  display: grid;
  justify-items: center;
  gap: 0.35rem;
  padding: 0.55rem 0.2rem;
  border-radius: var(--radius-md);
  color: var(--ink-muted);
  background: transparent;
  transition: background-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);

  span {
    font-size: 0.73rem;
    font-weight: 700;
  }

  &:hover,
  &.active {
    background: var(--chrome-hover);
    color: var(--ink);
    transform: translateY(-1px);
  }
}

@media (max-width: 960px) {
  .shell-body {
    grid-template-columns: 1fr;
    max-height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 1rem);
    min-height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 1rem);
    padding-bottom: 1rem;
  }

  .sidebar {
    display: none;
  }

  .workspace {
    height: auto;
    max-height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 1rem);
  }

  .bottom-nav {
    display: grid;
  }

  .app-shell {
    padding-bottom: calc(var(--bottom-nav-height) + 1rem);
  }

  .overlay-card {
    padding: 0.75rem 0.75rem 1rem;
  }

  .overlay-stack {
    inset: var(--topbar-height) 0 calc(var(--bottom-nav-height) + 0.35rem) 0;
  }

  .overlay-card :deep(.page-wrapper) {
    width: 100%;
    max-height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 1.35rem);
    min-height: 0;
    overflow: auto;
  }

  .overlay-card :deep(.event-sheet) {
    width: 100%;
  }
}

@media (max-width: 720px) {
  .brand-block img {
    width: 2.4rem;
    height: 2.4rem;
  }

  .topbar {
    padding-inline: 0.75rem;
  }

  .brand-kicker {
    font-size: 0.72rem;
  }

  .brand-block h1 {
    font-size: 1rem;
  }

  .action-btn span {
    display: none;
  }
}
</style>
