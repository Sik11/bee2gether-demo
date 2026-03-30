<script setup>
import { computed, ref, watchEffect } from 'vue';
import { pages } from '../store/pages';
import Page from './helper/Page.vue';
import { sendJoinEvent, sendLeaveEvent, removeEvent, events, findEventAttendees, toggleSavedEvent } from '../store/events';
import { auth } from '../store/auth';
import { userLocation } from '../store/userLocation';
import heartBackground from '../assets/heart-background-full.png';
import Avatar from './helper/Avatar.vue';
import { formatDistanceLabel, formatEventDate } from '../utils/eventMeta';

const msg = ref('');
const showJoin = ref(true);
const isSaved = computed(() => events.isEventSaved(events.selected.id));
const isOwner = computed(() => events.selected.userId === auth.user.userId);
const distanceLabel = computed(() => formatDistanceLabel(userLocation.location, events.selected));

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

function backtoMap() {
  msg.value = '';
  events.clearSelectedEvent();
  pages.dropLayer();
}

async function saveEvent() {
  const response = await toggleSavedEvent(auth.user.userId, events.selected.id);
  msg.value = response.msg || '';
}

async function copyEventLink() {
  const url = new URL(window.location.href);
  url.searchParams.set('tab', pages.selected);
  url.searchParams.set('event', events.selected.id);
  await navigator.clipboard.writeText(url.toString());
  msg.value = 'Link copied';
}

watchEffect(() => {
  if (!events.selected.attendees) {
    return;
  }

  showJoin.value = !events.selected.attendees.some(attendee => attendee.userId === auth.user.userId);
});
</script>

<template>
  <Page title="Event Info">
    <article id="form" class="soft-panel">
      <div class="img-container">
        <img v-if="events.selected['eventImg(s)'][0]" :src="events.selected['eventImg(s)'][0]" alt="Event image" />
        <img v-else :src="heartBackground" alt="Event image" />
      </div>

      <div class="info-container">
        <p class="date">{{ events.selected.time }}</p>
        <h2 class="name">{{ events.selected.name }}</h2>

        <section>
          <p class="sub-title">Description</p>
          <p class="description">{{ events.selected.description }}</p>
        </section>

        <section v-if="events.selected.tags?.length">
          <p class="sub-title">Tags</p>
          <ul class="tags">
            <li v-for="tag in events.selected.tags" :key="tag">{{ tag }}</li>
          </ul>
        </section>

        <section>
          <p class="sub-title">Snapshot</p>
          <div class="meta-grid">
            <span class="meta-chip">{{ formatEventDate(events.selected.time) }}</span>
            <span class="meta-chip">{{ events.selected.attendees?.length || 0 }} attending</span>
            <span class="meta-chip">{{ distanceLabel }}</span>
            <span class="meta-chip">{{ events.selected.groupId ? 'Group event' : 'Open event' }}</span>
          </div>
        </section>

        <section>
          <p class="sub-title">Organiser</p>
          <div class="account">
            <Avatar :username="events.selected.username" custom-class="pfp"/>
            <div class="text">
              <div class="username">{{ events.selected.username }}</div>
              <div class="id">#{{ auth.user.userId.substring(0, 6) }}</div>
            </div>
          </div>
        </section>

        <section>
          <p class="sub-title">Attendees</p>
          <div v-if="events.selected.attendees?.length" class="attendees">
            <div class="account" v-for="attendee in events.selected.attendees" :key="attendee.userId">
              <Avatar :username="attendee.username" custom-class="pfp"/>
              <div class="text">
                <div class="username">{{ attendee.username }}</div>
                <div class="id">#{{ attendee.userId.substring(0, 6) }}</div>
              </div>
            </div>
          </div>
          <p v-else class="section-copy">No attendees yet.</p>
        </section>
      </div>
    </article>

    <div class="action-row">
      <button v-if="isOwner" class="btn btn-danger overview-btn" @click="onDelete">Delete Event</button>
      <button v-else-if="showJoin" class="btn btn-primary overview-btn" @click="join">Join Event</button>
      <button v-else class="btn btn-secondary overview-btn" @click="leave">Leave Event</button>
      <button class="btn btn-secondary overview-btn" @click="saveEvent">{{ isSaved ? 'Saved' : 'Interested' }}</button>
      <button class="btn btn-secondary overview-btn" @click="copyEventLink">Copy Link</button>
      <button class="btn btn-secondary overview-btn" @click="backtoMap">Back To Map</button>
    </div>

    <p v-if="msg === 'OK'" class="success-msg">Success!</p>
    <p v-else class="error-msg">{{ msg }}</p>
  </Page>
</template>

<style scoped lang="scss">
#form {
  border-radius: var(--radius-lg);
  overflow: hidden;
  text-align: left;

  .img-container {
    width: 100%;
    height: clamp(15rem, 34vw, 23rem);
    overflow: hidden;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .info-container {
    display: grid;
    gap: 1rem;
    padding: 1.15rem;
  }

  .date {
    margin: 0;
    color: var(--ink-muted);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .name {
    margin: -0.4rem 0 0;
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 3vw, 2.5rem);
    line-height: 0.98;
    letter-spacing: -0.05em;
  }

  .sub-title {
    margin: 0 0 0.5rem;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--ink-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .description,
  .tags {
    margin: 0;
    color: var(--ink-soft);
    line-height: 1.65;
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    padding: 0;
    list-style: none;
  }

  .tags li {
    padding: 0.5rem 0.8rem;
    border-radius: var(--radius-pill);
    background: var(--accent-soft);
    color: var(--accent-strong);
    font-weight: 700;
  }

  .meta-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
  }

  .meta-chip {
    padding: 0.5rem 0.8rem;
    border-radius: var(--radius-pill);
    background: var(--surface-strong);
    color: var(--ink);
    font-weight: 700;
    border: 1px solid var(--border);
  }

  .account {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.6rem 0 0;
    min-height: 3.2rem;

    .pfp {
      width: 3rem;
      height: 3rem;
      border-radius: 100%;
      overflow: hidden;
    }

    .text {
      min-width: 0;
    }

    .username {
      font-size: 1rem;
      font-weight: 700;
    }

    .id {
      font-size: 0.82rem;
      color: var(--ink-muted);
    }
  }
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.overview-btn {
  flex: 1 1 12rem;
}

.success-msg {
  color: var(--success);
}

.error-msg {
  color: var(--danger);
}

@media (max-width: 640px) {
  .action-row {
    flex-direction: column;
  }
}
</style>
