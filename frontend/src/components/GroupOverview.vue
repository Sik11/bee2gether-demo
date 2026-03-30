<script setup>
import { computed } from 'vue';
import { pages } from '../store/pages';
import { groups, joinUserGroup } from "../store/groups.js";
import Page from './helper/Page.vue';
import { events } from '../store/events.js';
import heartBackground from '../assets/heart-background.png';
import { auth } from '../store/auth';
import { formatEventDate } from '../utils/eventMeta';

const emit = defineEmits(['backToMap']);

const isGroupJoined = computed(() => {
  return groups.userGroups.some(userGroup => userGroup.id === groups.currentGroup.id);
});

async function joinGroup() {
  if (!isGroupJoined.value) {
    await joinUserGroup(groups.currentGroup.id);
  }
}

function backtoMap() {
  groups.clearSelectedGroup();
  pages.dropLayer();
  emit("backToMap");
}

function clickedEvent(event) {
  events.selectEvent(event);
}

const groupEvents = computed(() => groups.currentGroup.events);
const currentTitle = computed(() => groups.currentGroup.name);
const isOwner = computed(() => groups.currentGroup.userId === auth.user.userId);

function createGroupEvent() {
  groups.currentGroupIdForEvents = groups.currentGroup.id;
  pages.addLayer('create-event');
}
</script>

<template>
  <Page :title="currentTitle">
    <section class="group-overview-form soft-panel">
      <p class="eyebrow">Group overview</p>
      <h2>{{ groups.currentGroup.name }}</h2>
      <p class="section-copy">{{ groups.currentGroup.description }}</p>
      <div class="group-meta">
        <span class="meta-chip">{{ groups.currentGroup.memberCount || 0 }} members</span>
        <span class="meta-chip">{{ groups.currentGroup.upcomingEventCount || 0 }} upcoming events</span>
        <span class="meta-chip">{{ isOwner ? 'You own this group' : 'Joined group' }}</span>
      </div>
    </section>

    <div class="action-row">
      <button v-if="!isGroupJoined" class="btn btn-primary overview-btn" @click="joinGroup">Join group</button>
      <button v-else type="button" class="btn btn-primary overview-btn" @click="createGroupEvent">
        Create group event
      </button>
      <button class="btn btn-secondary overview-btn" @click="backtoMap">Back</button>
    </div>

    <div v-if="!groupEvents?.length" class="empty-state soft-panel">
      <h3>No group events yet</h3>
      <p class="section-copy">Create the first shared plan for this group and it will appear here.</p>
    </div>

    <div v-else class="events-container">
      <article v-for="event in groupEvents" :key="event.id" class="event-card soft-panel">
        <div class="event-image">
          <img :src="event['eventImg(s)'][0] || heartBackground" alt="Event image" />
        </div>
        <div class="event-copy">
          <p class="event-date">{{ new Date(event.time).toLocaleDateString() }}</p>
          <h3 class="event-name">{{ event.name }}</h3>
          <p class="event-description">{{ formatEventDate(event.time) }} · {{ event.attendees?.length || 0 }} attending</p>
        </div>
        <button class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">View details</button>
      </article>
    </div>
  </Page>
</template>

<style scoped lang="scss">
.group-overview-form {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  padding: 1.25rem;
  border-radius: var(--radius-lg);

  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 3vw, 2.4rem);
    letter-spacing: -0.05em;
  }
}

.group-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.meta-chip {
  padding: 0.5rem 0.8rem;
  border-radius: var(--radius-pill);
  background: var(--surface-strong);
  border: 1px solid var(--border);
  color: var(--ink);
  font-weight: 700;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.overview-btn {
  flex: 1 1 12rem;
}

.events-container {
  display: grid;
  gap: 1rem;
}

.event-card {
  border-radius: var(--radius-lg);
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-image {
  width: 5.5rem;
  aspect-ratio: 1 / 1;
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-right: 1rem;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.event-copy {
  min-width: 0;
  margin-right: auto;
}

.event-date {
  margin: 0;
  font-size: 0.82rem;
  color: var(--ink-muted);
}

.event-name {
  margin: 0.4rem 0 0;
  font-weight: 700;
}

.event-description {
  margin: 0.35rem 0 0;
  color: var(--ink-soft);
}

.empty-state {
  padding: 1.35rem;
  border-radius: var(--radius-lg);
}

@media (max-width: 720px) {
  .action-row,
  .event-card {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
