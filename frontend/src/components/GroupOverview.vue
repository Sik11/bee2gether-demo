<script setup>
import { computed } from 'vue';
import { pages } from '../store/pages'
import { groups, joinUserGroup } from "../store/groups.js";  // Import joinUserGroup
import Page from './helper/Page.vue';
import { auth } from '../store/auth';
import { getEvents } from '../store/events.js';


const emit = defineEmits(['backToMap']);

const isGroupJoined = computed(() => {
  return groups.userGroups.some(userGroup => userGroup.id === groups.currentGroup.id);
});

const title = groups.currentGroup.name;

// Updated joinGroup function to use joinUserGroup
async function joinGroup() {
    if (!isGroupJoined.value) {
        console.log("Joining group");
        const response = await joinUserGroup(groups.currentGroup.id);
        if (response.result) {
            console.log("Joined group successfully");
            // Optionally, emit an event or take additional action upon successful join
        } else {
            console.error(response.msg || "Failed to join group");
        }
    } else {
        console.log("Already in group");
    }
}

function backtoMap() {
    pages.dropLayer();
    emit("backToMap");
}

function clickedEvent(event) {
  getEvents().selected = event;
  pages.addLayer('event-overview');
}

const groupEvents = computed(() => {
    return groups.currentGroup.events;
});

const currentTitle = computed(() => {
    return groups.currentGroup.name;
});

function createGroupEvent(){
    groups.currentGroupIdForEvents = groups.currentGroup.id;
    pages.addLayer('create-event');
}
</script>

<template>
  <Page :title="currentTitle">
    <form class="event-overview-form">
        <h2>Description</h2>
        <p>{{ groups.currentGroup.description }}</p>
    </form>
    <button v-if="!isGroupJoined" class="overview-btn" @click="joinGroup">Join</button>
    <button v-else type="button" class="overview-btn" @click="createGroupEvent">
      Create Group Event
    </button>
    <button class="overview-btn" @click="backtoMap">Back</button>
    <div class="events-container">
      <div v-for="event in groupEvents" :key="event.id" class="event-card">
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
        <button class="more-info-btn"  @click="clickedEvent(event)" >More info...</button>
      </div>
    </div>
  </Page>
</template>


<style scoped lang="scss">

.event-overview-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    h2 {
        margin: 0;
        margin-bottom: 20px;
        font-weight: bold;
    }
}

.overview-btn {
    width: 100%; /* Full width buttons */
    padding: 0.5rem; /* Padding inside buttons */
    border-radius: 25px; /* Rounded corners for buttons */
    border: none; /* No border for buttons */
    color: white; /* Text color for buttons */
    font-weight: bold; /* Bold font for button text */
    cursor: pointer; /* Cursor change for hover */
    background-color: #FFC01F;
    margin: 0.5rem 0;

    &:hover {
        background-color: #000000;
    }
  }


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

</style>

