<script setup>
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { pages } from '../store/pages';
import Page from './helper/Page.vue';
import { getEvents, updateSavedEvents, updateUserEvents } from '../store/events.js';
import { auth } from '../store/auth';
import { userLocation } from '../store/userLocation';
import heartBackground from '../assets/heart-background.png';
import { formatDistanceLabel, formatEventDate } from '../utils/eventMeta';
import { getScheduleExportUrl } from '../api';

const title = "Your Events";
const userId = auth.user.userId;
const route = useRoute();
const router = useRouter();

const viewOptions = [
  { id: 'attending', label: 'Attending' },
  { id: 'saved', label: 'Saved' },
  { id: 'agenda', label: 'Agenda' },
  { id: 'month', label: 'Month' },
];

const userEvents = computed(() => getEvents().userEvents);
const savedEvents = computed(() => getEvents().savedEvents);
const ownedEventIds = computed(() => new Set(userEvents.value.filter((event) => event.userId === userId).map((event) => event.id)));
const currentView = computed(() => viewOptions.some((item) => item.id === route.query.eventsView) ? route.query.eventsView : 'attending');

const planningEvents = computed(() => {
  const merged = [...userEvents.value, ...savedEvents.value];
  const seen = new Map();
  for (const event of merged) {
    if (!seen.has(event.id)) {
      seen.set(event.id, event);
    }
  }
  return [...seen.values()].sort((a, b) => new Date(a.time) - new Date(b.time));
});

const agendaGroups = computed(() => {
  const groups = new Map();
  for (const event of planningEvents.value) {
    const key = formatEventDate(event.time);
    const current = groups.get(key) || [];
    current.push(event);
    groups.set(key, current);
  }
  return [...groups.entries()];
});

function toLocalDateKey(dateLike) {
  const date = new Date(dateLike);
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

const monthGrid = computed(() => {
  const today = new Date();
  const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const firstDay = new Date(firstOfMonth);
  firstDay.setDate(firstDay.getDate() - ((firstOfMonth.getDay() + 6) % 7));

  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(firstDay);
    day.setDate(firstDay.getDate() + index);
    const key = toLocalDateKey(day);
    const eventsForDay = planningEvents.value.filter((event) => {
      return toLocalDateKey(event.time) === key;
    });
    return {
      key,
      day,
      events: eventsForDay,
      inMonth: day.getMonth() === today.getMonth(),
      isToday: key === toLocalDateKey(today),
    };
  });
});

onMounted(async () => {
  updateUserEvents(userId);
  updateSavedEvents(userId);
});

function clickedEvent(event) {
  getEvents().selectEvent(event);
}

function setView(view) {
  router.replace({ query: { ...route.query, eventsView: view } });
}

const scheduleExportUrl = computed(() => (
  auth.user?.userId ? getScheduleExportUrl(auth.user.userId) : '#'
));
const canExportSchedule = computed(() => Boolean(auth.user?.userId));
</script>

<template>
  <Page :title="title">
    <section class="summary soft-panel">
      <div>
        <p class="eyebrow">Your plans</p>
        <h2 class="section-title">{{ planningEvents.length }} items across attending and saved</h2>
      </div>
      <div class="summary-actions">
        <a
          v-if="canExportSchedule"
          class="btn btn-secondary"
          :href="scheduleExportUrl"
          download
        >
          Export schedule
        </a>
        <button type="button" class="btn btn-primary" @click="pages.addLayer('create-event')">Create Event</button>
      </div>
    </section>

    <p v-if="!canExportSchedule" class="section-copy export-note">
      Calendar export is only available once a signed-in user session is active.
    </p>

    <div class="tab-row">
      <button
        v-for="option in viewOptions"
        :key="option.id"
        type="button"
        :class="['tab-btn', { active: currentView === option.id }]"
        @click="setView(option.id)"
      >
        {{ option.label }}
      </button>
    </div>

    <section v-if="currentView === 'attending'" class="events-section">
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
    </section>

    <section v-else-if="currentView === 'saved'" class="events-section">
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
    </section>

    <section v-else-if="currentView === 'agenda'" class="events-section">
      <div class="section-heading">
        <h3>Agenda</h3>
        <p class="section-copy">Everything upcoming, grouped by date.</p>
      </div>
      <div v-if="!agendaGroups.length" class="empty-state soft-panel">
        <h3>No upcoming plans yet</h3>
        <p class="section-copy">Joined and saved events will appear here automatically.</p>
      </div>
      <div v-else class="agenda-list">
        <section v-for="[label, agendaEvents] in agendaGroups" :key="label" class="agenda-group soft-panel">
          <h3>{{ label }}</h3>
          <article v-for="event in agendaEvents" :key="event.id" class="agenda-item">
            <div>
              <p class="event-date">{{ formatEventDate(event.time) }}</p>
              <h4>{{ event.name }}</h4>
              <p class="section-copy">{{ event.attendees?.length || 0 }} attending · {{ event.groupId ? 'Group event' : 'Open event' }}</p>
            </div>
            <button type="button" class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">Open</button>
          </article>
        </section>
      </div>
    </section>

    <section v-else class="events-section">
      <div class="section-heading">
        <h3>Month</h3>
        <p class="section-copy">A calendar view of upcoming plans.</p>
      </div>
      <div class="month-grid soft-panel">
        <article v-for="cell in monthGrid" :key="cell.key" :class="['month-cell', { muted: !cell.inMonth, today: cell.isToday }]">
          <div class="month-day">{{ cell.day.getDate() }}</div>
          <button
            v-for="event in cell.events.slice(0, 2)"
            :key="event.id"
            type="button"
            class="month-event"
            @click="clickedEvent(event)"
          >
            {{ event.name }}
          </button>
          <span v-if="cell.events.length > 2" class="month-more">+{{ cell.events.length - 2 }} more</span>
        </article>
      </div>
    </section>
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

.summary-actions,
.tab-row,
.events-container,
.events-section,
.agenda-list {
  display: flex;
  gap: 0.75rem;
}

.summary-actions,
.tab-row {
  flex-wrap: wrap;
}

.export-note {
  margin: -0.3rem 0 0;
}

.tab-btn {
  padding: 0.7rem 1rem;
  border-radius: var(--radius-pill);
  background: var(--surface-strong);
  border: 1px solid var(--border);
  color: var(--ink-soft);
}

.tab-btn.active {
  background: var(--accent-soft);
  color: var(--accent-strong);
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
}

.events-container,
.events-section,
.agenda-list {
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

.event-badge,
.month-more {
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

.event-name,
.agenda-group h3,
.agenda-item h4 {
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

.empty-state,
.agenda-group,
.month-grid {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
}

.agenda-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border);
}

.agenda-item .more-info-btn {
  min-height: 3.15rem;
  padding-inline: 1.35rem;
  border-radius: var(--radius-pill);
  align-self: center;
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.75rem;
}

.month-cell {
  min-height: 7.5rem;
  padding: 0.65rem;
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  border: 1px solid var(--border);
  display: grid;
  align-content: start;
  gap: 0.45rem;
}

.month-cell.today {
  border-color: color-mix(in srgb, var(--accent) 64%, var(--border));
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--accent-soft) 76%, transparent), transparent 58%),
    var(--surface-strong);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 34%, transparent);
}

.month-cell.muted {
  opacity: 0.55;
}

.month-day {
  font-weight: 700;
}

.month-cell.today .month-day {
  color: var(--accent-strong);
}

.month-event {
  text-align: left;
  padding: 0.35rem 0.5rem;
  border-radius: var(--radius-sm);
  background: var(--accent-soft);
  color: var(--accent-strong);
}

@media (max-width: 820px) {
  .summary {
    flex-direction: column;
    align-items: stretch;
  }

  .event-card,
  .agenda-item {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .event-image {
    width: 100%;
    aspect-ratio: 16 / 9;
  }

  .month-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
