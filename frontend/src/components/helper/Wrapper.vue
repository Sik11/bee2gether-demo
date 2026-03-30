<script setup>
import { computed } from 'vue';
import { mdiThemeLightDark, mdiPlus } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { auth } from '../../store/auth';
import { pages } from '../../store/pages';
import { settings } from '../../store/settings';
import logo from '../../assets/logo.png';
import darkLogo from '../../assets/dark-logo.png';

const navItems = computed(() => pages.getLabelledTabs());
const topbarCreateHiddenPages = ["map", "events", "account"];
const showTopbarCreateAction = computed(() => !topbarCreateHiddenPages.includes(pages.selected));

const toggleTheme = () => {
  settings.isDarkMode = !settings.isDarkMode;
};

const select = (id) => {
  pages.setSelected(id);
};
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand-block">
        <img :src="settings.isDarkMode ? darkLogo : logo" alt="Logo saying Bee 2 Gether with a happy bee ontop"/>
        <div>
          <p class="brand-kicker">Bee2Gether</p>
          <h1>Hello, {{ auth.user.username }}</h1>
        </div>
      </div>
      <div class="topbar-actions">
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
            v-for="({ id, label }) in navItems"
            :key="id"
            type="button"
            :class="['nav-item', { active: pages.isSelected(id) }]"
            @click="select(id)"
          >
            <svg-icon :path="label.icon" height="1.15rem"/>
            <span>{{ label.text }}</span>
          </button>
        </nav>
      </aside>

      <main class="workspace">
        <div class="page-stack">
          <template v-for="({ component, id, props, label }) in pages.tabs" :key="id">
            <div
              v-if="pages.isVisible(id)"
              :class="['page', {
                visible: pages.isVisible(id),
                overlay: !label,
                stacked: pages.layers.includes(id)
              }]"
              :style="{ zIndex: pages.getZIndex(id) }"
            >
              <component :is="component" v-bind="props"/>
            </div>
          </template>
        </div>
      </main>
    </div>

    <nav class="bottom-nav soft-panel">
      <button
        v-for="({ id, label }) in navItems"
        :key="id"
        type="button"
        :class="['bottom-nav__item', { active: pages.isSelected(id) }]"
        @click="select(id)"
      >
        <svg-icon :path="label.icon" height="1.25rem"/>
        <span>{{ label.text }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped lang="scss">
.app-shell {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding-bottom: calc(var(--bottom-nav-height) + 1rem);
  background: var(--canvas);
  color: var(--ink);
  transition: background-color var(--transition-base), color var(--transition-base);
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
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
}

.theme-btn:hover {
  background: var(--chrome-hover);
  color: var(--ink);
  transform: translateY(-1px);
}

.shell-body {
  flex: 1;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  gap: 1rem;
  padding: 0 1rem 1rem;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  border-radius: var(--radius-lg);
  background: var(--chrome-surface);
}

.sidebar-spacer {
  min-height: 2.85rem;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
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
  min-width: 0;
  background: var(--canvas);
  transition: background-color var(--transition-base);
}

.page-stack {
  position: relative;
  min-height: calc(100dvh - var(--topbar-height) - 1.5rem);
}

.page {
  position: absolute;
  inset: 0;
  background: transparent;
  opacity: 0;
  transform: translateY(0.75rem);
  pointer-events: none;
  transition: opacity var(--transition-base), transform var(--transition-base);

  &.visible {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
  }

  &.overlay {
    inset: 1rem clamp(0.25rem, 2vw, 1.25rem) 1rem;
    border-radius: var(--radius-lg);
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-lg);
    overflow: auto;
  }
}

.bottom-nav {
  position: fixed;
  left: 1rem;
  right: 1rem;
  bottom: 1rem;
  z-index: 45;
  display: none;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.25rem;
  padding: 0.45rem;
  border-radius: var(--radius-lg);
}

.bottom-nav__item {
  min-height: 4.25rem;
  padding: 0.6rem 0.45rem;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--ink-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  transition: background-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);

  &:hover {
    background: var(--chrome-hover);
    color: var(--ink);
  }

  &.active {
    background: var(--accent-soft);
    color: var(--ink);
  }
}

.bottom-nav__item :deep(svg) {
  color: var(--nav-icon);
}

.bottom-nav__item:hover :deep(svg),
.bottom-nav__item.active :deep(svg) {
  color: var(--nav-icon-active);
}

@media (max-width: 1024px) {
  .shell-body {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }

  .topbar {
    padding-bottom: 0.75rem;
  }

  .action-btn span {
    display: none;
  }

  .action-btn {
    width: 2.9rem;
    padding-inline: 0;
  }

  .page-stack {
    min-height: calc(100dvh - var(--topbar-height) - var(--bottom-nav-height) - 1.5rem);
  }

  .page.overlay {
    inset: 0;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }

  .bottom-nav {
    display: grid;
  }
}

@media (max-width: 640px) {
  .topbar {
    padding-inline: 0.85rem;
  }

  .brand-block h1 {
    font-size: 1rem;
  }

  .brand-kicker {
    display: none;
  }
}
</style>
