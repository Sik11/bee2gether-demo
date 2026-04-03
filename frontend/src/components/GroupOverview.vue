<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { pages } from '../store/pages';
import { groups, joinUserGroup } from "../store/groups.js";
import Page from './helper/Page.vue';
import { events } from '../store/events.js';
import heartBackground from '../assets/heart-background.png';
import { auth } from '../store/auth';
import { getGroupChatMessages, sendGroupChatMessage } from '../api';
import { formatEventDate, formatEventTimeRange } from '../utils/eventMeta';
import { addRealtimeListener, subscribeRealtimeChannel, unsubscribeRealtimeChannel } from '../store/realtime';

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
  pages.dropLayer('group-overview');
  emit("backToMap");
}

function clickedEvent(event) {
  events.selectEvent(event);
}

const groupEvents = computed(() => groups.currentGroup.events);
const currentTitle = computed(() => groups.currentGroup.name);
const isOwner = computed(() => groups.currentGroup.userId === auth.user.userId);
const chatMessages = ref([]);
const chatBody = ref('');
let removeRealtimeListener = null;
let subscribedChannel = null;

const chatFeed = computed(() => [...chatMessages.value].sort((a, b) => (
  new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
)));

function isOwnMessage(message) {
  return message?.userId === auth.user?.userId;
}

function formatChatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date.toLocaleString(undefined, {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function createGroupEvent() {
  groups.currentGroupIdForEvents = groups.currentGroup.id;
  pages.addLayer('create-event');
}

async function refreshChat() {
  if (!groups.currentGroup.id || !auth.user?.userId || !isGroupJoined.value) {
    chatMessages.value = [];
    return;
  }
  const response = await getGroupChatMessages(groups.currentGroup.id, auth.user.userId);
  if (response.result) {
    chatMessages.value = response.messages || [];
  }
}

async function sendMessage() {
  if (!chatBody.value.trim()) {
    return;
  }
  const response = await sendGroupChatMessage(groups.currentGroup.id, auth.user.userId, chatBody.value.trim());
  if (response.result) {
    chatBody.value = '';
    if (response.message && !chatMessages.value.some((message) => message.id === response.message.id)) {
      chatMessages.value.push(response.message);
    }
  }
}

watch(
  () => groups.currentGroup.id,
  async (groupId, previousGroupId) => {
    if (previousGroupId) {
      unsubscribeRealtimeChannel(`group:${previousGroupId}`);
    }
    if (!groupId) {
      chatMessages.value = [];
      return;
    }

    subscribedChannel = `group:${groupId}`;
    subscribeRealtimeChannel(subscribedChannel);
    await refreshChat();
  },
  { immediate: true }
);

onMounted(() => {
  removeRealtimeListener = addRealtimeListener('group.chat.message.created', (detail) => {
    if (detail.groupId !== groups.currentGroup.id || !detail.message) {
      return;
    }
    if (!chatMessages.value.some((message) => message.id === detail.message.id)) {
      chatMessages.value.push(detail.message);
    }
  });
});

onUnmounted(() => {
  removeRealtimeListener?.();
  if (subscribedChannel) {
    unsubscribeRealtimeChannel(subscribedChannel);
  }
});
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

    <section v-else class="events-panel soft-panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">Upcoming plans</p>
          <h3>What the group is doing next</h3>
        </div>
        <span class="section-count">{{ groupEvents.length }} event<span v-if="groupEvents.length !== 1">s</span></span>
      </div>
      <div class="events-container">
      <article v-for="event in groupEvents" :key="event.id" class="event-card">
        <div class="event-image">
          <img :src="event['eventImg(s)'][0] || heartBackground" alt="Event image" />
        </div>
        <div class="event-copy">
          <p class="event-date">{{ formatEventDate(event) }}</p>
          <h3 class="event-name">{{ event.name }}</h3>
          <p class="event-description">{{ formatEventTimeRange(event) }} · {{ event.attendees?.length || 0 }} attending</p>
        </div>
        <button class="btn btn-secondary detail-btn" @click="clickedEvent(event)">View details</button>
      </article>
      </div>
    </section>

    <section v-if="isGroupJoined" class="chat-panel soft-panel">
      <div class="chat-head">
        <div>
          <p class="eyebrow">Group chat</p>
          <h3>Talk to the hive</h3>
        </div>
        <button type="button" class="btn btn-secondary chat-action-btn" @click="refreshChat">Reload history</button>
      </div>
      <div v-if="chatFeed.length" class="chat-list">
        <article
          v-for="message in chatFeed"
          :key="message.id"
          :class="['chat-message', { 'chat-message--own': isOwnMessage(message) }]"
        >
          <div class="chat-meta">
            <strong>{{ message.username }}</strong>
            <span>{{ formatChatTimestamp(message.createdAt) }}</span>
          </div>
          <p>{{ message.body }}</p>
        </article>
      </div>
      <p v-else class="section-copy">No messages yet.</p>
      <div class="chat-compose">
        <textarea v-model="chatBody" class="textarea" rows="3" placeholder="Send a message to the group"></textarea>
        <button type="button" class="btn btn-primary" @click="sendMessage">Send message</button>
      </div>
    </section>
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
  padding-inline: 0.35rem;
  align-items: stretch;
}

.overview-btn {
  flex: 1 1 12rem;
  min-height: 3.35rem;
  padding-inline: 1.35rem;
  justify-content: center;
}

.events-panel,
.chat-panel,
.empty-state {
  padding: 1.25rem;
  border-radius: var(--radius-lg);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.4rem;
}

.section-head h3 {
  margin: 0.28rem 0 0;
  font-family: var(--font-display);
  font-size: 1.28rem;
}

.section-count {
  padding: 0.45rem 0.78rem;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--surface-muted) 84%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 82%, transparent);
  color: var(--ink-soft);
  font-size: 0.82rem;
  font-weight: 700;
}

.events-container {
  display: grid;
  gap: 0;
}

.event-card {
  padding: 1rem 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border-top: 1px solid color-mix(in srgb, var(--border) 82%, transparent);
}

.event-card:first-child {
  border-top: 0;
  padding-top: 0.2rem;
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

.detail-btn {
  min-height: 3.15rem;
  min-width: 8.25rem;
  padding-inline: 1.2rem;
  justify-content: center;
  flex: 0 0 auto;
}

.chat-panel {
  display: grid;
  gap: 1rem;
}

.chat-head,
.chat-meta {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.chat-head h3 {
  margin: 0.35rem 0 0;
  font-family: var(--font-display);
}

.chat-action-btn {
  min-height: 3.15rem;
  padding-inline: 1.3rem;
  border-radius: var(--radius-pill);
  align-self: center;
  flex: 0 0 auto;
}

.chat-list {
  display: grid;
  gap: 0.6rem;
  padding: 0.85rem;
  border-radius: calc(var(--radius-lg) - 8px);
  background: color-mix(in srgb, var(--surface-muted) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 82%, transparent);
  max-height: 18rem;
  overflow: auto;
}

.chat-message {
  max-width: min(34rem, 84%);
  padding: 0.82rem 0.95rem;
  border-radius: 1.15rem;
  background: var(--surface-strong);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  justify-self: start;
}

.chat-message--own {
  justify-self: end;
  background: color-mix(in srgb, var(--accent-soft) 48%, var(--surface-strong));
  border-color: color-mix(in srgb, var(--accent) 24%, var(--border));
}

.chat-message p {
  margin: 0.22rem 0 0;
  color: var(--ink-soft);
  line-height: 1.45;
}

.chat-meta {
  align-items: baseline;
}

.chat-meta strong {
  font-size: 0.92rem;
}

.chat-meta span {
  color: var(--ink-muted);
  font-size: 0.72rem;
}

.chat-compose {
  display: grid;
  gap: 0.85rem;
  padding: 0.85rem;
  border-radius: calc(var(--radius-lg) - 8px);
  background: color-mix(in srgb, var(--surface-muted) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 78%, transparent);
}

.chat-compose .btn {
  justify-self: end;
  min-height: 3.15rem;
  padding-inline: 1.3rem;
  border-radius: var(--radius-pill);
}

@media (max-width: 720px) {
  .action-row,
  .event-card {
    flex-direction: column;
    align-items: stretch;
  }

  .overview-btn {
    flex: 0 0 auto;
    min-height: 3.15rem;
  }

  .chat-head,
  .chat-meta,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .action-row {
    padding-inline: 0;
  }

  .chat-panel {
    padding: 1rem;
  }

  .chat-list,
  .chat-compose {
    padding: 0.75rem;
  }

  .detail-btn,
  .chat-action-btn {
    width: 100%;
  }

  .chat-message {
    max-width: 100%;
  }

  .chat-compose .btn {
    width: 100%;
    justify-self: stretch;
  }
}
</style>
