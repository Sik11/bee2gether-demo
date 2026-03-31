<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  mdiAccountGroup,
  mdiClose,
  mdiContentCopy,
  mdiDeleteOutline,
  mdiHeartOutline,
  mdiMapMarker,
} from '@mdi/js';
import EventSheetMap from './helper/EventSheetMap.vue';
import svgIcon from './helper/svg-icon.vue';
import Avatar from './helper/Avatar.vue';
import { pages } from '../store/pages';
import { sendJoinEvent, sendLeaveEvent, removeEvent, events, findEventAttendees, toggleSavedEvent } from '../store/events';
import { auth } from '../store/auth';
import { userLocation } from '../store/userLocation';
import { addEventComment, deleteEventComment, getEventComments, getEventExportUrl } from '../api';
import { formatDistanceLabel, formatEventDate, formatEventDateWithRange, formatEventTimeRange } from '../utils/eventMeta';
import { settings } from '../store/settings';
import logo from '../assets/logo.png';
import darkLogo from '../assets/dark-logo.png';

const msg = ref('');
const showJoin = ref(true);
const comments = ref([]);
const commentBody = ref('');

const activeLogo = computed(() => (settings.isDarkMode ? darkLogo : logo));
const isSaved = computed(() => events.isEventSaved(events.selected.id));
const isOwner = computed(() => events.selected.userId === auth.user.userId);
const distanceLabel = computed(() => formatDistanceLabel(userLocation.location, events.selected));
const summaryTitle = computed(() => events.selected.placeName || events.selected.name || 'Event location');
const summarySubtitle = computed(() => {
  const placeAddress = events.selected.placeAddress;
  if (placeAddress) {
    return placeAddress;
  }
  if (distanceLabel.value) {
    return `${distanceLabel.value} · ${events.selected.lat?.toFixed?.(4) ?? '--'}, ${events.selected.long?.toFixed?.(4) ?? '--'}`;
  }
  return `${events.selected.lat?.toFixed?.(4) ?? '--'}, ${events.selected.long?.toFixed?.(4) ?? '--'}`;
});
const eventExportUrl = computed(() => (events.selected.id ? getEventExportUrl(events.selected.id) : '#'));

const join = async () => {
  const response = await sendJoinEvent(auth.user.userId, auth.user.username, events.selected.id);
  events.selected.attendees = await findEventAttendees(events.selected.id);
  msg.value = response.msg || '';
};

const leave = async () => {
  const response = await sendLeaveEvent(auth.user.userId, events.selected.id);
  events.selected.attendees = await findEventAttendees(events.selected.id);
  msg.value = response.msg || '';
};

const onDelete = async () => {
  await removeEvent(events.selected.id, auth.user.userId);
  msg.value = '';
  events.clearSelectedEvent();
  pages.dropLayer();
};

function closeSheet() {
  msg.value = '';
  events.clearSelectedEvent();
  pages.dropLayer('event-overview');
}

async function saveEvent() {
  const response = await toggleSavedEvent(auth.user.userId, events.selected.id);
  msg.value = response.msg || '';
}

async function copyEventLink() {
  const url = new URL(window.location.href);
  url.pathname = '/events';
  url.searchParams.set('event', events.selected.id);
  await navigator.clipboard.writeText(url.toString());
  msg.value = 'Link copied';
}

async function loadComments() {
  if (!events.selected.id) {
    comments.value = [];
    return;
  }
  const response = await getEventComments(events.selected.id);
  comments.value = response.comments || [];
}

async function postComment() {
  if (!commentBody.value.trim()) {
    return;
  }
  const response = await addEventComment(events.selected.id, auth.user.userId, commentBody.value.trim());
  if (response.result) {
    commentBody.value = '';
    await loadComments();
  }
}

async function removeComment(commentId) {
  const response = await deleteEventComment(events.selected.id, commentId, auth.user.userId);
  if (response.result) {
    await loadComments();
  }
}

watch(() => events.selected.id, loadComments, { immediate: true });

watch(() => events.selected.attendees, () => {
  if (!events.selected.attendees) {
    return;
  }

  showJoin.value = !events.selected.attendees.some((attendee) => attendee.userId === auth.user.userId);
}, { immediate: true });

onMounted(loadComments);
</script>

<template>
  <section class="event-sheet soft-panel event-sheet--view">
    <header class="event-sheet__header">
      <div class="event-sheet__identity">
        <img :src="activeLogo" alt="Bee2Gether logo" />
        <span>Bee2Gether</span>
        <span class="event-sheet__divider"></span>
        <strong>Event details</strong>
      </div>
      <button type="button" class="event-sheet__icon-btn" aria-label="Close event info" @click="closeSheet">
        <svg-icon :path="mdiClose" width="1.1rem" height="1.1rem" />
      </button>
    </header>

    <div class="event-sheet__body">
      <section class="event-sheet__main">
        <div class="event-sheet__intro">
          <p class="eyebrow">Event info</p>
          <h2>{{ events.selected.name }}</h2>
          <p>{{ events.selected.description || 'No description yet.' }}</p>
        </div>

        <div class="event-hero" v-if="events.selected['eventImg(s)']?.[0]">
          <img :src="events.selected['eventImg(s)'][0]" alt="Event cover" />
        </div>

        <section class="detail-stack">
          <div class="detail-grid">
            <div class="detail-block">
              <span class="detail-label">When</span>
              <strong>{{ formatEventDateWithRange(events.selected) }}</strong>
            </div>
            <div class="detail-block">
              <span class="detail-label">Time</span>
              <strong>{{ formatEventTimeRange(events.selected) }}</strong>
            </div>
            <div class="detail-block">
              <span class="detail-label">Attendance</span>
              <strong>{{ events.selected.attendees?.length || 0 }} going</strong>
            </div>
            <div class="detail-block">
              <span class="detail-label">Type</span>
              <strong>{{ events.selected.groupId ? 'Group event' : 'Open event' }}</strong>
            </div>
            <div class="detail-block">
              <span class="detail-label">Distance</span>
              <strong>{{ distanceLabel }}</strong>
            </div>
            <div class="detail-block" v-if="events.selected.placeName || events.selected.placeAddress">
              <span class="detail-label">Place</span>
              <strong>{{ events.selected.placeName || events.selected.placeAddress }}</strong>
            </div>
          </div>

          <div class="organiser-row">
            <Avatar :username="events.selected.username" custom-class="organiser-row__avatar" />
            <div>
              <span class="detail-label">Organiser</span>
              <strong>{{ events.selected.username }}</strong>
              <small>#{{ events.selected.userId?.substring(0, 6) }}</small>
            </div>
          </div>

          <div v-if="events.selected.tags?.length" class="tag-row">
            <span v-for="tag in events.selected.tags" :key="tag" class="tag-pill">{{ tag }}</span>
          </div>

          <details class="fold-section">
            <summary>
              <span>Attendees</span>
              <span>{{ events.selected.attendees?.length || 0 }}</span>
            </summary>
            <div class="fold-section__body">
              <div v-if="events.selected.attendees?.length" class="attendees-list">
                <div v-for="attendee in events.selected.attendees" :key="attendee.userId" class="attendee-row">
                  <Avatar :username="attendee.username" custom-class="attendee-row__avatar" />
                  <div>
                    <strong>{{ attendee.username }}</strong>
                    <small>#{{ attendee.userId.substring(0, 6) }}</small>
                  </div>
                </div>
              </div>
              <p v-else class="section-copy">No attendees yet.</p>
            </div>
          </details>

          <details class="fold-section">
            <summary>
              <span>Comments</span>
              <span>{{ comments.length }}</span>
            </summary>
            <div class="fold-section__body fold-section__body--comments">
              <div class="comment-compose">
                <textarea v-model="commentBody" class="textarea" rows="3" placeholder="Add a comment for this event"></textarea>
                <button type="button" class="btn btn-primary" @click="postComment">Post comment</button>
              </div>
              <div v-if="comments.length" class="comments-list">
                <article v-for="comment in comments" :key="comment.id" class="comment-card">
                  <div class="comment-head">
                    <strong>{{ comment.username }}</strong>
                    <button
                      v-if="comment.userId === auth.user.userId || isOwner"
                      type="button"
                      class="comment-delete"
                      @click="removeComment(comment.id)"
                    >
                      Remove
                    </button>
                  </div>
                  <p>{{ comment.body }}</p>
                </article>
              </div>
              <p v-else class="section-copy">No comments yet.</p>
            </div>
          </details>
        </section>

        <p v-if="msg === 'OK'" class="success-msg">Success!</p>
        <p v-else-if="msg" class="error-msg">{{ msg }}</p>
      </section>

      <aside class="event-sheet__side">
        <div class="side-pane">
          <EventSheetMap
            :coordinates="{ lat: events.selected.lat, lng: events.selected.long }"
            :user-coordinates="userLocation.location"
            :summary-title="summaryTitle"
            :summary-subtitle="summarySubtitle"
          />
        </div>
      </aside>
    </div>

    <footer class="event-sheet__footer event-sheet__footer--wrap">
      <button v-if="isOwner" class="btn btn-danger" @click="onDelete">
        <svg-icon :path="mdiDeleteOutline" width="1rem" height="1rem" />
        <span>Delete</span>
      </button>
      <button v-else-if="showJoin" class="btn btn-primary" @click="join">
        <svg-icon :path="mdiAccountGroup" width="1rem" height="1rem" />
        <span>Join event</span>
      </button>
      <button v-else class="btn btn-secondary" @click="leave">
        <svg-icon :path="mdiAccountGroup" width="1rem" height="1rem" />
        <span>Leave event</span>
      </button>
      <button class="btn btn-secondary" @click="saveEvent">
        <svg-icon :path="mdiHeartOutline" width="1rem" height="1rem" />
        <span>{{ isSaved ? 'Saved' : 'Interested' }}</span>
      </button>
      <button class="btn btn-secondary" @click="copyEventLink">
        <svg-icon :path="mdiContentCopy" width="1rem" height="1rem" />
        <span>Copy link</span>
      </button>
      <a class="btn btn-secondary" :href="eventExportUrl">
        <svg-icon :path="mdiMapMarker" width="1rem" height="1rem" />
        <span>Export .ics</span>
      </a>
      <button class="btn btn-secondary" @click="closeSheet">Close</button>
    </footer>
  </section>
</template>

<style scoped lang="scss">
.event-sheet {
  width: min(100%, 69rem);
  height: min(43rem, calc(100dvh - var(--topbar-height) - 1.55rem));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: calc(var(--radius-lg) + 0.3rem);
  border: 1px solid color-mix(in srgb, var(--border-strong) 88%, transparent);
  background: color-mix(in srgb, var(--surface) 95%, transparent);
  box-shadow:
    0 28px 70px rgba(23, 18, 12, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
}

.event-sheet__header,
.event-sheet__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 1rem 1.2rem;
  border-bottom: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
}

.event-sheet__footer {
  justify-content: flex-end;
  border-bottom: none;
  border-top: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
  background: color-mix(in srgb, var(--surface) 98%, transparent);
  padding-block: 1.1rem;
  padding-inline: 1.35rem;
}

.event-sheet__footer--wrap {
  flex-wrap: wrap;
}

.event-sheet__identity {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: var(--ink-soft);
  font-size: 0.96rem;

  img {
    width: 1.65rem;
    height: 1.65rem;
  }

  strong {
    color: var(--ink);
    font-weight: 700;
  }
}

.event-sheet__divider {
  width: 1px;
  height: 1.15rem;
  background: color-mix(in srgb, var(--border) 95%, transparent);
}

.event-sheet__icon-btn {
  width: 2.65rem;
  height: 2.65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  background: color-mix(in srgb, var(--surface) 96%, transparent);
  color: var(--ink);
}

.event-sheet__body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(22rem, 0.9fr);
}

.event-sheet__main,
.event-sheet__side {
  min-width: 0;
  min-height: 0;
}

.event-sheet__main {
  padding: 1.5rem 1.5rem 0;
  overflow: auto;
  overscroll-behavior: contain;
}

.event-sheet__side {
  padding: 1rem;
  border-left: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
  background: color-mix(in srgb, var(--surface-strong) 60%, transparent);
}

.side-pane {
  height: 100%;
}

.event-sheet__intro {
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1rem;

  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(2rem, 3vw, 2.7rem);
    line-height: 0.96;
    letter-spacing: -0.06em;
  }

  p {
    margin: 0;
    color: var(--ink-soft);
  }
}

.event-hero {
  overflow: hidden;
  border-radius: 1.45rem;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  margin-bottom: 1rem;

  img {
    display: block;
    width: 100%;
    height: 11.5rem;
    object-fit: cover;
  }
}

.detail-stack {
  display: grid;
  gap: 1rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
}

.detail-block,
.organiser-row,
.fold-section {
  padding: 0.95rem 1rem;
  border-radius: 1.25rem;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  background: color-mix(in srgb, var(--surface) 82%, transparent);
}

.detail-block {
  display: grid;
  gap: 0.25rem;

  strong {
    font-size: 0.98rem;
  }
}

.detail-label {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-muted);
}

.organiser-row {
  display: flex;
  align-items: center;
  gap: 0.8rem;

  strong,
  small {
    display: block;
  }

  small {
    color: var(--ink-muted);
    margin-top: 0.15rem;
  }
}

.organiser-row__avatar,
.attendee-row__avatar {
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 999px;
  overflow: hidden;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.42rem 0.72rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--accent-strong);
  font-weight: 700;
}

.fold-section summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  font-weight: 700;
  color: var(--ink);
  list-style: none;
}

.fold-section summary::-webkit-details-marker {
  display: none;
}

.fold-section__body {
  display: grid;
  gap: 0.8rem;
  padding-top: 0.85rem;
}

.fold-section__body--comments {
  gap: 0.9rem;
}

.attendees-list,
.comments-list,
.comment-compose {
  display: grid;
  gap: 0.7rem;
}

.attendee-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;

  strong,
  small {
    display: block;
  }

  small {
    color: var(--ink-muted);
  }
}

.textarea {
  min-height: 7.2rem;
  resize: vertical;
}

.comment-card {
  padding: 0.75rem 0.9rem;
  border-radius: 1rem;
  background: color-mix(in srgb, var(--surface-strong) 84%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);

  p {
    margin: 0.45rem 0 0;
    color: var(--ink-soft);
  }
}

.comment-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.comment-delete {
  border: none;
  background: transparent;
  color: var(--danger);
  font-weight: 700;
  cursor: pointer;
}

.section-copy,
.success-msg,
.error-msg {
  margin: 0;
}

.success-msg {
  color: var(--success);
}

.error-msg {
  color: var(--danger);
  font-weight: 700;
}

@media (max-width: 980px) {
  .event-sheet {
    width: min(100%, 48rem);
    height: min(45rem, calc(100dvh - var(--topbar-height) - 1rem));
  }

  .event-sheet__body {
    grid-template-columns: 1fr;
  }

  .event-sheet__side {
    border-left: none;
    border-top: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
  }
}

@media (max-width: 720px) {
  .event-sheet {
    width: min(100%, calc(100% - 0.8rem));
    height: calc(100dvh - var(--topbar-height) - 0.7rem);
    border-radius: 1.25rem;
  }

  .event-sheet__header,
  .event-sheet__footer {
    padding-inline: 0.95rem;
  }

  .event-sheet__main {
    padding: 1rem 1rem 0;
  }

  .event-sheet__side {
    padding: 0.9rem;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
