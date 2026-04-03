<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { pages } from '../store/pages';
import Page from './helper/Page.vue';
import { getEvents, preloadPersonalEventData, updateSavedEvents, updateUserEvents } from '../store/events.js';
import { auth } from '../store/auth';
import { userLocation } from '../store/userLocation';
import heartBackground from '../assets/heart-background.png';
import { formatDistanceLabel, formatEventDate, formatEventDay, formatEventTimeRange, parseEventDate, toLocalDateKey } from '../utils/eventMeta';
import { getPlanningEvents, getScheduleExportUrl } from '../api';

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
const userEventsTotal = computed(() => getEvents().userEventsTotal || userEvents.value.length);
const savedEventsTotal = computed(() => getEvents().savedEventsTotal || savedEvents.value.length);
const totalPlans = computed(() => userEventsTotal.value + savedEventsTotal.value);
const loadingAttending = computed(() => getEvents().loadingUserEvents && !getEvents().hasLoadedUserEvents);
const loadingSaved = computed(() => getEvents().loadingSavedEvents && !getEvents().hasLoadedSavedEvents);
const loadingPlanning = ref(false);
const ownedEventIds = computed(() => new Set(userEvents.value.filter((event) => event.userId === userId).map((event) => event.id)));
const currentView = computed(() => viewOptions.some((item) => item.id === route.query.eventsView) ? route.query.eventsView : 'attending');
const PAGE_SIZE = 5;
const attendingPage = ref(0);
const savedPage = ref(0);
const agendaPage = ref(0);
const agendaEvents = ref([]);
const agendaTotal = ref(0);
const monthEvents = ref([]);

const planningEvents = computed(() => {
  const merged = currentView.value === 'month' ? [...monthEvents.value] : [...agendaEvents.value];
  const seen = new Map();
  for (const event of merged) {
    if (!seen.has(event.id)) {
      seen.set(event.id, event);
    }
  }
  return [...seen.values()].sort((a, b) => (parseEventDate(a)?.getTime() || 0) - (parseEventDate(b)?.getTime() || 0));
});

const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const selectedMonthDayKey = ref(toLocalDateKey(new Date()));

const agendaGroups = computed(() => {
  const groups = new Map();
  for (const event of planningEvents.value) {
    const key = formatEventDay(event);
    const current = groups.get(key) || [];
    current.push(event);
    groups.set(key, current);
  }
  return [...groups.entries()];
});

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
      return toLocalDateKey(event) === key;
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

const selectedMonthCell = computed(() => (
  monthGrid.value.find((cell) => cell.key === selectedMonthDayKey.value)
  || monthGrid.value.find((cell) => cell.isToday)
  || monthGrid.value.find((cell) => cell.events.length)
  || monthGrid.value[0]
));

const selectedMonthEvents = computed(() => selectedMonthCell.value?.events || []);
const selectedMonthHeading = computed(() => {
  if (!selectedMonthCell.value) {
    return '';
  }
  return selectedMonthCell.value.day.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
});

watch(monthGrid, (grid) => {
  if (!grid.length) {
    return;
  }
  const existing = grid.find((cell) => cell.key === selectedMonthDayKey.value);
  if (existing) {
    return;
  }
  selectedMonthDayKey.value = (grid.find((cell) => cell.isToday) || grid.find((cell) => cell.events.length) || grid[0]).key;
}, { immediate: true });

onMounted(async () => {
  preloadPersonalEventData(userId);
  await loadCurrentView();
});

watch(currentView, async () => {
  await loadCurrentView();
});

async function loadCurrentView() {
  if (currentView.value === 'attending') {
    await updateUserEvents(userId, { offset: attendingPage.value * PAGE_SIZE, limit: PAGE_SIZE });
    return;
  }
  if (currentView.value === 'saved') {
    await updateSavedEvents(userId, { offset: savedPage.value * PAGE_SIZE, limit: PAGE_SIZE });
    return;
  }

  loadingPlanning.value = true;
  try {
    if (currentView.value === 'agenda') {
      const response = await getPlanningEvents(userId, { offset: agendaPage.value * PAGE_SIZE, limit: PAGE_SIZE });
      agendaEvents.value = response?.events || [];
      agendaTotal.value = Number(response?.total || agendaEvents.value.length);
      return;
    }

    const today = new Date();
    const monthKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
    const response = await getPlanningEvents(userId, { month: monthKey, offset: 0, limit: 50 });
    monthEvents.value = response?.events || [];
  } finally {
    loadingPlanning.value = false;
  }
}

function clickedEvent(event) {
  getEvents().selectEvent(event);
}

function setView(view) {
  router.replace({ query: { ...route.query, eventsView: view } });
}

async function changePage(kind, direction) {
  if (kind === 'attending') {
    attendingPage.value = Math.max(0, attendingPage.value + direction);
  } else if (kind === 'saved') {
    savedPage.value = Math.max(0, savedPage.value + direction);
  } else {
    agendaPage.value = Math.max(0, agendaPage.value + direction);
  }
  await loadCurrentView();
}

function selectMonthDay(key) {
  selectedMonthDayKey.value = key;
}

function formatMonthEventTime(event) {
  const date = parseEventDate(event);
  if (!date) {
    return '';
  }
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(date);
}

const scheduleExportUrl = computed(() => (
  auth.user?.userId ? getScheduleExportUrl(auth.user.userId) : '#'
));
const canExportSchedule = computed(() => Boolean(auth.user?.userId));
const attendingHasPrev = computed(() => attendingPage.value > 0);
const attendingHasNext = computed(() => (attendingPage.value + 1) * PAGE_SIZE < userEventsTotal.value);
const savedHasPrev = computed(() => savedPage.value > 0);
const savedHasNext = computed(() => (savedPage.value + 1) * PAGE_SIZE < savedEventsTotal.value);
const agendaHasPrev = computed(() => agendaPage.value > 0);
const agendaHasNext = computed(() => (agendaPage.value + 1) * PAGE_SIZE < agendaTotal.value);
</script>

<template>
  <Page :title="title">
    <section class="summary soft-panel">
      <div>
        <p class="eyebrow">Your plans</p>
        <h2 class="section-title">{{ totalPlans }} items across attending and saved</h2>
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
      <div v-if="loadingAttending" class="events-container">
        <article v-for="item in 3" :key="`attending-skeleton-${item}`" class="event-card soft-panel event-card--skeleton">
          <div class="event-image skeleton-block"></div>
          <div class="event-copy">
            <div class="event-badges">
              <span class="event-badge skeleton-pill"></span>
              <span class="event-badge skeleton-pill"></span>
            </div>
            <div class="skeleton-line skeleton-line--short"></div>
            <div class="skeleton-line skeleton-line--title"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line skeleton-line--wide"></div>
          </div>
          <div class="more-info-btn skeleton-button"></div>
        </article>
      </div>
      <div v-else-if="!userEvents.length" class="empty-state soft-panel">
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
            <p class="event-date">{{ formatEventDate(event) }}</p>
            <h3 class="event-name">{{ event.name }}</h3>
            <p class="event-description">{{ event.description || 'No description yet.' }}</p>
            <p class="event-meta">{{ formatEventTimeRange(event) }} · {{ event.attendees?.length || 0 }} attending · {{ formatDistanceLabel(userLocation.location, event) }}</p>
          </div>
          <button class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">View details</button>
        </article>
      </div>
      <div v-if="userEventsTotal > PAGE_SIZE" class="pager">
        <button type="button" class="btn btn-secondary" :disabled="!attendingHasPrev" @click="changePage('attending', -1)">Previous</button>
        <span class="pager-copy">Showing {{ attendingPage * PAGE_SIZE + 1 }}-{{ Math.min((attendingPage + 1) * PAGE_SIZE, userEventsTotal) }} of {{ userEventsTotal }}</span>
        <button type="button" class="btn btn-secondary" :disabled="!attendingHasNext" @click="changePage('attending', 1)">Next</button>
      </div>
    </section>

    <section v-else-if="currentView === 'saved'" class="events-section">
      <div class="section-heading">
        <h3>Saved</h3>
        <p class="section-copy">Events you marked as interesting without joining.</p>
      </div>
      <div v-if="loadingSaved" class="events-container">
        <article v-for="item in 3" :key="`saved-skeleton-${item}`" class="event-card soft-panel event-card--skeleton">
          <div class="event-image skeleton-block"></div>
          <div class="event-copy">
            <div class="event-badges">
              <span class="event-badge skeleton-pill"></span>
              <span class="event-badge skeleton-pill"></span>
            </div>
            <div class="skeleton-line skeleton-line--short"></div>
            <div class="skeleton-line skeleton-line--title"></div>
            <div class="skeleton-line"></div>
          </div>
          <div class="more-info-btn skeleton-button"></div>
        </article>
      </div>
      <div v-else-if="!savedEvents.length" class="empty-state soft-panel">
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
            <p class="event-date">{{ formatEventDate(event) }}</p>
            <h3 class="event-name">{{ event.name }}</h3>
            <p class="event-description">{{ event.description || 'No description yet.' }}</p>
            <p class="event-meta">{{ formatEventTimeRange(event) }}</p>
          </div>
          <button class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">View details</button>
        </article>
      </div>
      <div v-if="savedEventsTotal > PAGE_SIZE" class="pager">
        <button type="button" class="btn btn-secondary" :disabled="!savedHasPrev" @click="changePage('saved', -1)">Previous</button>
        <span class="pager-copy">Showing {{ savedPage * PAGE_SIZE + 1 }}-{{ Math.min((savedPage + 1) * PAGE_SIZE, savedEventsTotal) }} of {{ savedEventsTotal }}</span>
        <button type="button" class="btn btn-secondary" :disabled="!savedHasNext" @click="changePage('saved', 1)">Next</button>
      </div>
    </section>

    <section v-else-if="currentView === 'agenda'" class="events-section">
      <div class="section-heading">
        <h3>Agenda</h3>
        <p class="section-copy">Everything upcoming, grouped by date.</p>
      </div>
      <div v-if="loadingPlanning" class="agenda-list">
        <section v-for="item in 2" :key="`agenda-skeleton-${item}`" class="agenda-group soft-panel agenda-group--skeleton">
          <div class="skeleton-line skeleton-line--title"></div>
          <div v-for="row in 2" :key="`agenda-row-${item}-${row}`" class="agenda-item">
            <div class="agenda-item__copy">
              <div class="skeleton-line skeleton-line--short"></div>
              <div class="skeleton-line skeleton-line--title"></div>
              <div class="skeleton-line"></div>
            </div>
            <div class="more-info-btn skeleton-button"></div>
          </div>
        </section>
      </div>
      <div v-else-if="!agendaGroups.length" class="empty-state soft-panel">
        <h3>No upcoming plans yet</h3>
        <p class="section-copy">Joined and saved events will appear here automatically.</p>
      </div>
      <div v-else class="agenda-list">
        <section v-for="[label, agendaEvents] in agendaGroups" :key="label" class="agenda-group soft-panel">
          <h3>{{ label }}</h3>
          <article v-for="event in agendaEvents" :key="event.id" class="agenda-item">
            <div>
              <p class="event-date">{{ formatEventDate(event) }}</p>
              <h4>{{ event.name }}</h4>
              <p class="section-copy">{{ formatEventTimeRange(event) }} · {{ event.attendees?.length || 0 }} attending · {{ event.groupId ? 'Group event' : 'Open event' }}</p>
            </div>
            <button type="button" class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">Open</button>
          </article>
        </section>
      </div>
      <div v-if="agendaTotal > PAGE_SIZE" class="pager">
        <button type="button" class="btn btn-secondary" :disabled="!agendaHasPrev" @click="changePage('agenda', -1)">Previous</button>
        <span class="pager-copy">Showing {{ agendaPage * PAGE_SIZE + 1 }}-{{ Math.min((agendaPage + 1) * PAGE_SIZE, agendaTotal) }} of {{ agendaTotal }}</span>
        <button type="button" class="btn btn-secondary" :disabled="!agendaHasNext" @click="changePage('agenda', 1)">Next</button>
      </div>
    </section>

    <section v-else class="events-section">
      <div class="section-heading">
        <h3>Month</h3>
        <p class="section-copy">A calendar view of upcoming plans with a focused day agenda.</p>
      </div>
      <div v-if="loadingPlanning" class="month-loading soft-panel">
        <div class="month-loading__grid">
          <span v-for="item in 14" :key="`month-skeleton-${item}`" class="month-loading__cell"></span>
        </div>
        <p class="section-copy">Loading your calendar…</p>
      </div>
      <section v-else class="month-shell soft-panel">
        <div class="month-weekdays" aria-hidden="true">
          <span v-for="day in weekdayLabels" :key="day">{{ day }}</span>
        </div>
        <div class="month-grid">
          <button
            v-for="cell in monthGrid"
            :key="cell.key"
            type="button"
            :class="['month-cell', { muted: !cell.inMonth, today: cell.isToday, selected: selectedMonthCell?.key === cell.key }]"
            @click="selectMonthDay(cell.key)"
          >
            <div class="month-cell__head">
              <span class="month-day">{{ cell.day.getDate() }}</span>
              <span v-if="cell.isToday" class="today-pill">Today</span>
            </div>
            <div class="month-cell__events">
              <span
                v-for="event in cell.events.slice(0, 2)"
                :key="event.id"
                class="month-event"
              >
                <strong>{{ formatMonthEventTime(event) }}</strong>
                <span>{{ event.name }}</span>
              </span>
              <span v-if="cell.events.length > 2" class="month-more">+{{ cell.events.length - 2 }} more</span>
            </div>
          </button>
        </div>
      </section>

      <section class="month-focus soft-panel">
        <div class="month-focus__head">
          <div>
            <p class="eyebrow">{{ selectedMonthCell?.isToday ? 'Today' : 'Selected day' }}</p>
            <h4>{{ selectedMonthHeading }}</h4>
          </div>
          <span class="month-focus__count">{{ selectedMonthEvents.length }} event<span v-if="selectedMonthEvents.length !== 1">s</span></span>
        </div>

        <div v-if="selectedMonthEvents.length" class="month-focus__list">
          <article v-for="event in selectedMonthEvents" :key="`month-${event.id}`" class="month-focus__item">
            <div>
              <p class="event-date">{{ formatEventDate(event) }}</p>
              <h4>{{ event.name }}</h4>
              <p class="section-copy">{{ formatEventTimeRange(event) }} · {{ event.groupId ? 'Group event' : 'Open event' }}</p>
            </div>
            <button type="button" class="btn btn-secondary more-info-btn" @click="clickedEvent(event)">Open</button>
          </article>
        </div>
        <p v-else class="section-copy">No plans on this day.</p>
      </section>
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
.agenda-list,
.pager {
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

.pager {
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
}

.pager-copy {
  color: var(--ink-muted);
  font-size: 0.9rem;
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

.event-card--skeleton {
  pointer-events: none;
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

.skeleton-block,
.skeleton-line,
.skeleton-pill,
.skeleton-button,
.month-loading__cell {
  background:
    linear-gradient(
      90deg,
      var(--skeleton-edge) 0%,
      var(--skeleton-mid) 48%,
      var(--skeleton-base) 100%
    );
  background-size: 220% 100%;
  animation: skeleton-shift 1.6s ease-in-out infinite;
}

.skeleton-block {
  border-radius: var(--radius-md);
  min-height: 7.5rem;
}

.skeleton-line {
  height: 0.82rem;
  border-radius: 999px;
}

.skeleton-line--short {
  width: 28%;
}

.skeleton-line--title {
  width: 62%;
  height: 1.1rem;
}

.skeleton-line--wide {
  width: 78%;
}

.skeleton-pill {
  min-width: 5rem;
  min-height: 1.7rem;
}

.skeleton-button {
  width: 7.8rem;
  min-height: 3rem;
  border-radius: var(--radius-pill);
}

.empty-state,
.agenda-group,
.month-shell,
.month-focus {
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

.agenda-group--skeleton .agenda-item__copy {
  flex: 1;
  display: grid;
  gap: 0.55rem;
}

.agenda-item .more-info-btn {
  min-height: 3.15rem;
  padding-inline: 1.35rem;
  border-radius: var(--radius-pill);
  align-self: center;
  width: fit-content;
  min-width: 7.75rem;
  flex: 0 0 auto;
}

.month-shell {
  display: grid;
  gap: 0.9rem;
}

.month-loading {
  display: grid;
  gap: 1rem;
  padding: 1.4rem;
  border-radius: var(--radius-lg);
}

.month-loading__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.75rem;
}

.month-loading__cell {
  display: block;
  min-height: 7rem;
  border-radius: var(--radius-md);
}

.month-weekdays {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.75rem;
  min-width: 48rem;
  color: var(--ink-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.75rem;
  min-width: 48rem;
  overflow: visible;
}

.month-cell {
  min-height: 8.8rem;
  padding: 0.65rem;
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  border: 1px solid color-mix(in srgb, var(--border) 78%, transparent);
  display: grid;
  align-content: start;
  gap: 0.45rem;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--transition-fast), background-color var(--transition-fast), transform var(--transition-fast);
}

.month-cell.today {
  border-color: color-mix(in srgb, var(--accent) 34%, var(--border));
  background: color-mix(in srgb, var(--accent-soft) 10%, var(--surface-strong));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 14%, transparent);
}

.month-cell.selected {
  border-color: color-mix(in srgb, var(--accent) 48%, var(--border));
  background: color-mix(in srgb, var(--accent-soft) 15%, var(--surface-strong));
  transform: translateY(-1px);
}

.month-cell.muted {
  opacity: 0.55;
}

.month-cell__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
}

.month-day {
  font-weight: 700;
}

.month-cell.today .month-day {
  color: var(--accent-strong);
}

.today-pill {
  padding: 0.18rem 0.45rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--accent-strong);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.month-cell__events {
  display: grid;
  gap: 0.32rem;
}

.month-event {
  text-align: left;
  padding: 0.4rem 0.5rem;
  border-radius: var(--radius-sm);
  background: var(--accent-soft);
  color: var(--accent-strong);
  display: grid;
  gap: 0.12rem;
  font-size: 0.76rem;
  line-height: 1.25;
}

.month-event strong {
  font-size: 0.7rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.month-event span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.month-focus {
  display: grid;
  gap: 1rem;
}

.month-focus__head,
.month-focus__item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

@keyframes skeleton-shift {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.month-focus__head h4,
.month-focus__item h4 {
  margin: 0.25rem 0 0;
  font-size: 1.15rem;
}

.month-focus__count {
  padding: 0.45rem 0.75rem;
  border-radius: var(--radius-pill);
  background: var(--surface-strong);
  border: 1px solid var(--border);
  color: var(--ink-soft);
  font-weight: 700;
}

.month-focus__list {
  display: grid;
  gap: 0.8rem;
}

.month-focus__item {
  padding-top: 0.8rem;
  border-top: 1px solid var(--border);
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

  .month-shell {
    overflow-x: auto;
    padding-bottom: 0.9rem;
  }

  .month-weekdays,
  .month-grid {
    min-width: 40rem;
  }

  .month-cell {
    min-height: 7.8rem;
  }

  .month-focus__head,
  .month-focus__item {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 620px) {
  .month-shell,
  .month-focus {
    padding: 1rem;
  }

  .month-weekdays,
  .month-grid {
    min-width: 0;
    gap: 0.35rem;
  }

  .month-weekdays {
    font-size: 0.62rem;
    letter-spacing: 0.06em;
  }

  .month-cell {
    min-height: 5.35rem;
    padding: 0.45rem;
    border-radius: 1rem;
    gap: 0.3rem;
  }

  .month-cell__head {
    justify-content: flex-start;
  }

  .month-day {
    font-size: 0.92rem;
  }

  .today-pill {
    display: none;
  }

  .month-cell__events {
    display: flex;
    flex-wrap: wrap;
    gap: 0.22rem;
    margin-top: auto;
  }

  .month-event {
    width: 0.55rem;
    height: 0.55rem;
    padding: 0;
    border-radius: 999px;
    background: var(--accent);
    display: block;
    font-size: 0;
    min-height: 0;
  }

  .month-event strong,
  .month-event span {
    display: none;
  }

  .month-more {
    padding: 0;
    background: none;
    color: var(--accent-strong);
    font-size: 0.65rem;
    line-height: 1;
  }

  .month-focus__count {
    align-self: flex-start;
  }
}
</style>
