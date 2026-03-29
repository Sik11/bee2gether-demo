<script setup>
import { ref, onMounted,computed } from 'vue';
import { pages } from '../store/pages';
import Page from './helper/Page.vue';
import { getEvents, updateUserEvents } from '../store/events.js';
import { auth } from '../store/auth';

const title = "Your Events"

const userId = auth.user.userId;

// Reactive computed property to always get the latest events
const userEvents = computed(() => getEvents().userEvents);

onMounted(async () => {
  updateUserEvents(userId)
});

function clickedEvent(event) {
  getEvents().selected = event;
  pages.addLayer('event-overview');
}

</script>

<template>
  <Page :title="title">
    <div class="events-container">
      <div v-for="event in userEvents" :key="event.id" class="event-card">
        <div v-if="event['eventImg(s)'][0]" class="event-image">
          <img :src="event['eventImg(s)'][0]" alt="Event image" />
        </div>
        <div v-else class="event-image"> 
          <img src="../assets/heart-background.png" alt="Placeholder image" />
        </div>
        <div class="event-info">
          <div class="event-date">{{ new Date(event.time).toLocaleDateString() }}</div>
          <div class="event-name">{{ event.name }}</div>
        </div>
        <button class="more-info-btn" @click="clickedEvent(event)">More info...</button>
      </div>
    </div>

    <!-- Button placed outside the .events-container to fix it at the bottom -->
    <button type="button" class="create-event-btn" @click="pages.addLayer('create-event')">
      Create New Event
    </button> 
  </Page>
</template>

<style scoped lang="scss">

.events-container {
  padding: 1rem;
  max-height: 65vh; // Adjust height calculation as needed
  overflow-y: auto;
}

.event-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  height: 15vh;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  }
}

.event-image {
  flex-shrink: 0;
  width: 100px; // Set width of image box
  height: 100px; // Set height of image box
  border-radius: 8px;
  overflow: hidden;
  margin-right: 1rem;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover; // Ensures image covers the box
  }
}



.event-info {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: left;
}

.event-date {
  font-size: 0.85rem;
  color: #666;
}

.event-name {
  font-weight: bold;
}

.more-info-btn {
  border: none;
  background-color: transparent;
  color: #FFC01F;
  cursor: pointer;
  align-self: flex-end;
}

.create-event-btn {
  // Existing styles
  bottom: 20px; // Adjust position from bottom
}


.create-event-btn {
  background-color: #FFC01F; /* Replace with the specific color you need */
  color: white;
  font-weight: bold;
  border: none;
  border-radius: 30px; /* Adjust as needed */
  padding: 15px 30px;
  width: 90%; /* Adjust to match your layout */
  position: fixed;
  bottom: 5rem; /* Center the button */
  display: block;
  left: 50%;
  text-transform: uppercase; /* Optional: Makes text uppercase */
  transform: translateX(-50%);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Optional: Adds a shadow */
  cursor: pointer;
  transition: background-color 0.3s ease; /* Optional: Adds a transition effect */
}

.create-event-btn:hover {
  background-color: #e6b800; /* Darker shade for hover state */
}

</style>