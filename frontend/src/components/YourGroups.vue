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
const activeTab = ref('Your Groups');

onMounted(async () => {
  updateUserGroups(userId);
  updateGroups();
});

function groupOverview(group) {
  getGroups().selectGroup(group);
}

const switchTab = (tabName) => {
  activeTab.value = tabName;
};
</script>

<template>
  <Page :title="title">
    <section class="summary soft-panel">
      <div>
        <p class="eyebrow">Groups</p>
        <h2 class="section-title">{{ activeTab === 'Your Groups' ? userGroups.length : allGroups.length }} groups in view</h2>
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
</style>
