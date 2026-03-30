<script setup>
import { onMounted, computed } from 'vue';
import { pages } from '../store/pages';
import Page from './helper/Page.vue';
import { getEvents, updateSavedEvents, updateUserEvents } from '../store/events.js';
import { auth } from '../store/auth';
import { userLocation } from '../store/userLocation';
import heartBackground from '../assets/heart-background.png';
import { formatDistanceLabel, formatEventDate } from '../utils/eventMeta';

const title = "Your Events";
const userId = auth.user.userId;
const userEvents = computed(() => getEvents().userEvents);
const savedEvents = computed(() => getEvents().savedEvents);
const ownedEventIds = computed(() => new Set(userEvents.value.filter((event) => event.userId === userId).map((event) => event.id)));

onMounted(async () => {
  updateUserEvents(userId);
  updateSavedEvents(userId);
});

function clickedEvent(event) {
  getEvents().selectEvent(event);
}
</script>

<template>
  <Page :title="title">
    <section class="summary soft-panel">
      <div>
        <p class="eyebrow">Your plans</p>
        <h2 class="section-title">{{ userEvents.length + savedEvents.length }} active items across attending and saved</h2>
      </div>
      <button type="button" class="btn btn-primary" @click="pages.addLayer('create-event')">Create Event</button>
    </section>

    <div class="events-section">
      <div class="section-heading">
        <h3>Attending</h3>
        <p class="section-copy">Plans you created or joined.</p>
      </div>

      <div v-if="!userEvents.length" class="empty-state soft-panel">
        <h3>No attending events yet</h3>
        <p class="section-copy">Start with one plan and Bee2Gether will give your map something to discover.</p>
      </div>

      <div v-else class="events-container">
        <article v-for="event in userEvents" :key="event.id" class="event-card soft-panel">
          <div class="event-image">
            <img :src="event['eventImg(s)'][0] || heartBackground" alt="Event image" />
          </div>
          <div class="event-copy">
            <div class="event-badges">
              <span class="event-badge">{{ ownedEventIds.has(event.id) ? 'Owned' : 'Joined' }}</span>
              <span class="event-badge">{{ event.groupId ? 'Group event' : 'Open event' }}</span>
            </div>
            <p class="event-date">{{ formatEventDate(event.time) }}</p>
            <h3 class="event-name">{{ event.name }}</h3>
            <p class="event-description">{{ event.description || 'No description yet.' }}</p>
            <p class="event-meta">{{ event.attendees?.length || 0 }} attending · {{ formatDistanceLabel(userLocation.location, event) }}</p>
          </div>
          <button class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">View details</button>
        </article>
      </div>
    </div>

    <div class="events-section">
      <div class="section-heading">
        <h3>Saved</h3>
        <p class="section-copy">Events you marked as interesting without joining.</p>
      </div>

      <div v-if="!savedEvents.length" class="empty-state soft-panel">
        <h3>No saved events yet</h3>
        <p class="section-copy">Use the Interested action on any event to keep it close without joining it.</p>
      </div>

      <div v-else class="events-container">
        <article v-for="event in savedEvents" :key="`saved-${event.id}`" class="event-card soft-panel">
          <div class="event-image">
            <img :src="event['eventImg(s)'][0] || heartBackground" alt="Event image" />
          </div>
          <div class="event-copy">
            <div class="event-badges">
              <span class="event-badge">Saved</span>
              <span class="event-badge">{{ event.groupId ? 'Group event' : 'Open event' }}</span>
            </div>
            <p class="event-date">{{ formatEventDate(event.time) }}</p>
            <h3 class="event-name">{{ event.name }}</h3>
            <p class="event-description">{{ event.description || 'No description yet.' }}</p>
          </div>
          <button class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">View details</button>
        </article>
      </div>
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

.summary h2 {
  font-size: clamp(1.55rem, 2.6vw, 2.1rem);
}

.events-container {
  display: grid;
  gap: 1rem;
  padding-bottom: 1rem;
}

.events-section {
  display: grid;
  gap: 1rem;
}

.section-heading h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.25rem;
}

.event-card {
  display: grid;
  grid-template-columns: 7.5rem minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border-radius: var(--radius-lg);
}

.event-image {
  width: 7.5rem;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: var(--radius-md);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.event-copy {
  min-width: 0;
}

.event-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.event-badge {
  padding: 0.4rem 0.7rem;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 700;
  font-size: 0.78rem;
}

.event-date {
  margin: 0;
  color: var(--ink-muted);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.event-name {
  margin: 0.35rem 0 0.5rem;
  font-size: 1.25rem;
  line-height: 1.05;
}

.event-description {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.55;
}

.event-meta {
  margin: 0.45rem 0 0;
  color: var(--ink-muted);
  font-size: 0.85rem;
}

.more-info-btn {
  white-space: nowrap;
}

.empty-state {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  text-align: left;
}

.empty-state h3 {
  margin: 0 0 0.5rem;
  font-family: var(--font-display);
}

@media (max-width: 820px) {
  .summary {
    flex-direction: column;
    align-items: stretch;
  }

  .event-card {
    grid-template-columns: 1fr;
  }

  .event-image {
    width: 100%;
    aspect-ratio: 16 / 9;
  }
}
</style>
