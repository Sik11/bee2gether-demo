<script setup>
import { pages } from '../store/pages';
import { ref, onMounted, computed } from 'vue';
import { auth } from '../store/auth';
import Page from './helper/Page.vue';
import { getGroups, updateUserGroups, updateGroups } from '../store/groups.js';

const title = "Groups";
const userId = auth.user.userId;
const userGroups = computed(() => getGroups().userGroups);
const allGroups = computed(() => getGroups().availableGroups);
const userGroupsTotal = computed(() => getGroups().userGroupsTotal || userGroups.value.length);
const allGroupsTotal = computed(() => getGroups().availableGroupsTotal || allGroups.value.length);
const activeTab = ref('All Groups');
const PAGE_SIZE = 5;
const allGroupsPage = ref(0);
const userGroupsPage = ref(0);
const loadingGroups = computed(() => {
  if (activeTab.value === 'All Groups') {
    return getGroups().loadingAvailableGroups && !getGroups().hasLoadedAvailableGroups;
  }
  return getGroups().loadingUserGroups && !getGroups().hasLoadedUserGroups;
});

onMounted(async () => {
  await loadCurrentGroups();
});

async function loadCurrentGroups() {
  if (activeTab.value === 'Your Groups') {
    await updateUserGroups(userId, { offset: userGroupsPage.value * PAGE_SIZE, limit: PAGE_SIZE });
    return;
  }
  await updateGroups({ offset: allGroupsPage.value * PAGE_SIZE, limit: PAGE_SIZE });
}

function groupOverview(group) {
  getGroups().selectGroup(group);
}

const switchTab = (tabName) => {
  activeTab.value = tabName;
  loadCurrentGroups();
};

async function changeGroupPage(kind, direction) {
  if (kind === 'all') {
    allGroupsPage.value = Math.max(0, allGroupsPage.value + direction);
  } else {
    userGroupsPage.value = Math.max(0, userGroupsPage.value + direction);
  }
  await loadCurrentGroups();
}

const allGroupsHasPrev = computed(() => allGroupsPage.value > 0);
const allGroupsHasNext = computed(() => (allGroupsPage.value + 1) * PAGE_SIZE < allGroupsTotal.value);
const userGroupsHasPrev = computed(() => userGroupsPage.value > 0);
const userGroupsHasNext = computed(() => (userGroupsPage.value + 1) * PAGE_SIZE < userGroupsTotal.value);
</script>

<template>
  <Page :title="title">
    <section class="summary soft-panel">
      <div>
        <p class="eyebrow">Groups</p>
        <h2 class="section-title">{{ loadingGroups ? 'Loading groups…' : `${activeTab === 'Your Groups' ? userGroupsTotal : allGroupsTotal} groups in view` }}</h2>
      </div>
      <button type="button" class="btn btn-primary" @click="pages.addLayer('create-group')">
        Create Group
      </button>
    </section>

    <div class="tab-controls soft-panel">
      <button :class="['tab-btn', { active: activeTab === 'All Groups' }]" @click="switchTab('All Groups')">
        All Groups
      </button>
      <button :class="['tab-btn', { active: activeTab === 'Your Groups' }]" @click="switchTab('Your Groups')">
        Your Groups
      </button>
    </div>

    <div class="groups-container">
      <article v-if="loadingGroups" v-for="item in 3" :key="`group-skeleton-${item}`" class="group-card group-card--skeleton soft-panel">
        <div class="group-copy">
          <div class="group-badges">
            <span class="group-kicker skeleton-pill"></span>
            <span class="group-kicker skeleton-pill"></span>
          </div>
          <div class="skeleton-line skeleton-line--title"></div>
          <div class="skeleton-line"></div>
        </div>
        <div class="skeleton-button"></div>
      </article>
      <article v-for="group in activeTab === 'Your Groups' ? userGroups : allGroups" :key="group.id" class="group-card soft-panel">
        <div class="group-copy">
          <div class="group-badges">
            <span class="group-kicker">{{ group.userId === userId ? 'Owned' : activeTab === 'Your Groups' ? 'Member' : 'Community group' }}</span>
            <span class="group-kicker">{{ group.memberCount || 0 }} members</span>
            <span class="group-kicker">{{ group.upcomingEventCount || 0 }} upcoming</span>
          </div>
          <h3 class="group-name">{{ group.name }}</h3>
          <p class="group-description">{{ group.description || 'No description yet.' }}</p>
        </div>
        <button class="btn btn-secondary more-info-btn" @click="groupOverview(group)">View group</button>
      </article>
    </div>
    <div
      v-if="(activeTab === 'All Groups' ? allGroupsTotal : userGroupsTotal) > PAGE_SIZE"
      class="pager"
    >
      <button
        type="button"
        class="btn btn-secondary"
        :disabled="activeTab === 'All Groups' ? !allGroupsHasPrev : !userGroupsHasPrev"
        @click="changeGroupPage(activeTab === 'All Groups' ? 'all' : 'user', -1)"
      >
        Previous
      </button>
      <span class="pager-copy">
        Showing
        {{ (activeTab === 'All Groups' ? allGroupsPage : userGroupsPage) * PAGE_SIZE + 1 }}-{{
          Math.min(((activeTab === 'All Groups' ? allGroupsPage : userGroupsPage) + 1) * PAGE_SIZE, activeTab === 'All Groups' ? allGroupsTotal : userGroupsTotal)
        }}
        of {{ activeTab === 'All Groups' ? allGroupsTotal : userGroupsTotal }}
      </span>
      <button
        type="button"
        class="btn btn-secondary"
        :disabled="activeTab === 'All Groups' ? !allGroupsHasNext : !userGroupsHasNext"
        @click="changeGroupPage(activeTab === 'All Groups' ? 'all' : 'user', 1)"
      >
        Next
      </button>
    </div>
  </Page>
</template>

<style scoped lang="scss">
.summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border-radius: var(--radius-lg);
}

.groups-container {
  display: grid;
  gap: 1rem;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.pager-copy {
  color: var(--ink-muted);
  font-size: 0.9rem;
}

.group-card {
  border-radius: var(--radius-lg);
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.group-copy {
  min-width: 0;
}

.group-kicker {
  margin: 0;
  color: var(--ink-muted);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.35rem 0.65rem;
  border-radius: var(--radius-pill);
  background: var(--surface-strong);
  border: 1px solid var(--border);
}

.group-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.group-name {
  margin: 0.35rem 0 0.5rem;
  font-size: 1.25rem;
}

.group-description {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.55;
}

.more-info-btn {
  white-space: nowrap;
}

.group-card--skeleton {
  pointer-events: none;
}

.skeleton-pill {
  width: 5.5rem;
  height: 1.8rem;
  padding: 0;
  border-color: transparent;
  background:
    linear-gradient(120deg, var(--skeleton-edge), var(--skeleton-mid), var(--skeleton-base));
  background-size: 180% 100%;
  animation: skeleton-shift 1.2s ease-in-out infinite;
}

.skeleton-line {
  height: 0.92rem;
  margin-top: 0.65rem;
  border-radius: 999px;
  background:
    linear-gradient(120deg, var(--skeleton-edge), var(--skeleton-mid), var(--skeleton-base));
  background-size: 180% 100%;
  animation: skeleton-shift 1.2s ease-in-out infinite;
}

.skeleton-line--title {
  width: min(17rem, 72%);
  height: 1.5rem;
}

.skeleton-button {
  width: 8.5rem;
  height: 3rem;
  border-radius: var(--radius-pill);
  background:
    linear-gradient(120deg, var(--skeleton-edge), var(--skeleton-mid), var(--skeleton-base));
  background-size: 180% 100%;
  animation: skeleton-shift 1.2s ease-in-out infinite;
}

.tab-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  width: fit-content;
  padding: 0.35rem;
  border-radius: var(--radius-pill);
}

.tab-btn {
  min-height: 2.75rem;
  padding: 0.65rem 1rem;
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--ink-soft);
  font-weight: 700;
  cursor: pointer;
}

.tab-btn.active {
  background: var(--accent-soft);
  color: var(--ink);
}

@media (max-width: 720px) {
  .summary,
  .group-card {
    flex-direction: column;
    align-items: stretch;
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
