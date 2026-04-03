<script setup>
import { computed, onMounted } from 'vue';
import { markAllNotificationsRead, notifications, refreshNotifications } from '../store/notifications';
import { updateQueryState } from '../store/urlState';

const visibleNotifications = computed(() => notifications.items.slice(0, 10));

function closePanel() {
  updateQueryState({ notifications: null });
}

onMounted(async () => {
  await refreshNotifications();
  await markAllNotificationsRead();
});
</script>

<template>
  <aside class="notifications-panel soft-panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Notifications</p>
        <h2>Recent activity</h2>
      </div>
      <button type="button" class="btn btn-secondary" @click="closePanel">Close</button>
    </div>

    <div v-if="!notifications.items.length" class="empty">
      <h3>All caught up</h3>
      <p class="section-copy">New joins, comments, and group chat activity will show up here.</p>
    </div>

    <div v-else class="list">
      <article v-for="item in visibleNotifications" :key="item.id" class="notification-card">
        <p class="notification-type">{{ item.type.replace('-', ' ') }}</p>
        <h3>{{ item.title }}</h3>
        <p class="notification-body">{{ item.body }}</p>
      </article>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.notifications-panel {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 4;
  pointer-events: auto;
  width: min(20.5rem, calc(100vw - 2rem));
  max-height: calc(100% - 2rem);
  overflow: auto;
  padding: 1rem;
  border-radius: var(--radius-lg);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.panel-head h2 {
  margin: 0.35rem 0 0;
  font-family: var(--font-display);
  font-size: clamp(1.9rem, 3.4vw, 2.4rem);
  line-height: 0.95;
}

.list {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.notification-card {
  padding: 0.85rem 0.95rem;
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  border: 1px solid var(--border);
}

.notification-card h3,
.notification-card p {
  margin: 0;
}

.notification-card h3 {
  margin-top: 0.22rem;
  font-size: 0.98rem;
  line-height: 1.15;
  font-weight: 800;
}

.notification-type {
  color: var(--ink-muted);
  text-transform: uppercase;
  font-size: 0.68rem;
  letter-spacing: 0.05em;
}

.notification-body {
  margin-top: 0.18rem !important;
  font-size: 0.9rem;
  line-height: 1.35;
  color: var(--ink-soft);
}

.empty {
  padding: 1.25rem 0 0;
}

@media (max-width: 900px) {
  .notifications-panel {
    top: auto;
    bottom: 1rem;
    right: 1rem;
    width: min(20.5rem, calc(100vw - 2rem));
    max-height: min(28rem, calc(100% - 2rem));
  }
}
</style>
