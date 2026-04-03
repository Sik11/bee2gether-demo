<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { settings } from '../store/settings';
import { auth } from '../store/auth';
import { events } from '../store/events';
import { groups } from '../store/groups';
import { userLocation } from '../store/userLocation';
import { notifications } from '../store/notifications';
import Page from './helper/Page.vue';
import Avatar from './helper/Avatar.vue';

const router = useRouter();
const loadingAccountSummary = computed(() =>
  (events.loadingSavedEvents && !events.hasLoadedSavedEvents)
  || (events.loadingUserEvents && !events.hasLoadedUserEvents)
  || (groups.loadingUserGroups && !groups.hasLoadedUserGroups)
  || (notifications.loading && !notifications.hasLoaded)
);

const accountId = computed(() => {
  const userId = auth.user?.userId;
  return userId ? `#${userId.substring(0, 6)}` : '#guest';
});

const locationStatus = computed(() => {
  const { lat, lng } = userLocation.location;
  if (Number.isFinite(lat) && Number.isFinite(lng) && (lat !== 0 || lng !== 0)) {
    return 'Location active';
  }
  return 'Location unavailable';
});

function openNotifications() {
  router.replace({ query: { ...router.currentRoute.value.query, notifications: '1' } });
}

function logout() {
  auth.logout();
  router.replace('/auth');
}
</script>

<template>
  <Page title="Your Account" custom-class="body">
    <section class="hero soft-panel">
      <div class="header">
        <Avatar :username="auth.user.username" custom-class="pfp"/>
        <div class="hero-copy">
          <p class="eyebrow">Profile</p>
          <h2>{{ auth.user.username }}</h2>
          <p class="account-id">{{ accountId }}</p>
          <p class="section-copy">
            Keep your preferences light and your plans close. This is the fastest way back into discovery.
          </p>
        </div>
      </div>
      <div class="hero-actions">
        <button type="button" class="btn btn-secondary" @click="openNotifications">Open notifications</button>
        <button type="button" class="btn btn-danger" @click="logout">Logout</button>
      </div>
    </section>

    <section class="summary-grid">
      <template v-if="loadingAccountSummary">
        <article v-for="item in 4" :key="`account-skeleton-${item}`" class="summary-card summary-card--skeleton soft-panel">
          <div class="summary-head">
            <p class="eyebrow skeleton-pill"></p>
            <strong class="skeleton-number"></strong>
          </div>
          <p class="summary-copy skeleton-line"></p>
        </article>
      </template>
      <template v-else>
        <article class="summary-card soft-panel">
          <div class="summary-head">
            <p class="eyebrow">Saved</p>
            <strong>{{ events.savedEvents.length }}</strong>
          </div>
          <p class="summary-copy">Events you kept for later.</p>
        </article>
        <article class="summary-card soft-panel">
          <div class="summary-head">
            <p class="eyebrow">Joined</p>
            <strong>{{ events.userEvents.length }}</strong>
          </div>
          <p class="summary-copy">Plans already on your schedule.</p>
        </article>
        <article class="summary-card soft-panel">
          <div class="summary-head">
            <p class="eyebrow">Groups</p>
            <strong>{{ groups.userGroups.length }}</strong>
          </div>
          <p class="summary-copy">Communities you’re part of.</p>
        </article>
        <article class="summary-card soft-panel">
          <div class="summary-head">
            <p class="eyebrow">Alerts</p>
            <strong>{{ notifications.unreadCount }}</strong>
          </div>
          <p class="summary-copy">Unread activity waiting in notifications.</p>
        </article>
      </template>
    </section>

    <section class="settings-grid">
      <article class="settings-card soft-panel">
        <div class="settings-row">
          <div>
            <h3>Dark mode</h3>
            <p class="section-copy">Switch Bee2Gether into a richer night palette.</p>
          </div>
          <label class="toggle">
            <input v-model="settings.isDarkMode" type="checkbox" role="switch">
            <span></span>
          </label>
        </div>
      </article>

      <article class="settings-card soft-panel">
        <div class="settings-row">
          <div>
            <h3>Location status</h3>
            <p class="section-copy">Used for nearby discovery, distance labels, and map recentering.</p>
          </div>
          <strong class="status-pill">{{ locationStatus }}</strong>
        </div>
      </article>

      <article class="settings-card soft-panel full-width">
        <div class="settings-row">
          <div>
            <h3>Notifications</h3>
            <p class="section-copy">Recent joins, comments, and group chat updates stay one click away.</p>
          </div>
          <button type="button" class="btn btn-secondary" @click="openNotifications">Open</button>
        </div>
      </article>
    </section>
  </Page>
</template>

<style scoped lang="scss">
.body {
  text-align: left;
  gap: 1rem;
}

.hero,
.settings-card,
.summary-card {
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.hero {
  display: grid;
  gap: 1rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.full-width {
  grid-column: 1 / -1;
}

.summary-card {
  min-height: 10rem;
  display: grid;
  align-content: start;
  gap: 0.85rem;
}

.summary-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.summary-head strong {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 2.9rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.summary-copy {
  margin: 0;
  color: var(--ink-soft);
  max-width: 18rem;
}

.summary-card--skeleton {
  pointer-events: none;
}

.skeleton-pill,
.skeleton-number,
.skeleton-line {
  display: block;
  background:
    linear-gradient(120deg, var(--skeleton-edge), var(--skeleton-mid), var(--skeleton-base));
  background-size: 180% 100%;
  animation: skeleton-shift 1.2s ease-in-out infinite;
}

.skeleton-pill {
  width: 5.25rem;
  height: 1.7rem;
  border-radius: var(--radius-pill);
}

.skeleton-number {
  width: 3rem;
  height: 2.8rem;
  border-radius: 1rem;
}

.skeleton-line {
  width: 80%;
  height: 0.95rem;
  border-radius: 999px;
}

.header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;

  .pfp {
    width: clamp(5rem, 18vw, 8rem);
    height: clamp(5rem, 18vw, 8rem);
    border-radius: 100%;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
  }

  h2 {
    margin: 0.45rem 0 0.3rem;
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 4vw, 2.4rem);
    letter-spacing: -0.05em;
  }
}

.hero-copy {
  display: grid;
  gap: 0.15rem;
  align-content: start;
  max-width: 54rem;
}

.hero-copy .eyebrow {
  width: fit-content;
  max-width: 100%;
}

.hero-copy .section-copy {
  max-width: 42rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.account-id {
  margin: 0;
  color: var(--secondary);
  font-weight: 700;
}

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 100%;

  h3 {
    margin: 0 0 0.35rem;
    font-family: var(--font-display);
  }
}

.status-pill {
  padding: 0.55rem 0.8rem;
  border-radius: var(--radius-pill);
  background: var(--surface-strong);
  border: 1px solid var(--border);
}

.toggle {
  position: relative;
  display: inline-flex;
  width: 3.8rem;
  height: 2.2rem;

  input {
    position: absolute;
    inset: 0;
    opacity: 0;
  }

  span {
    width: 100%;
    height: 100%;
    border-radius: var(--radius-pill);
    background: var(--canvas-strong);
    border: 1px solid var(--border);
    transition: background-color var(--transition-fast);
    position: relative;
  }

  span::after {
    content: '';
    position: absolute;
    top: 0.22rem;
    left: 0.22rem;
    width: 1.45rem;
    height: 1.45rem;
    border-radius: 50%;
    background: var(--surface-strong);
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition-fast);
  }

  input:checked + span {
    background: var(--accent-soft);
  }

  input:checked + span::after {
    transform: translateX(1.55rem);
  }
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .header,
  .settings-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}

@keyframes skeleton-shift {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
</style>
