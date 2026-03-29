<script setup>
import { nextTick, ref } from 'vue';
import Page from './helper/Page.vue';
import svgIcon from './helper/svg-icon.vue';
import { mdiCamera, mdiMapMarker, mdiCrosshairsGps } from '@mdi/js';
import { userLocation } from "../store/userLocation.js";
import { pages } from '../store/pages';
import { auth } from '../store/auth';
import { addEvent } from "../store/events.js";
import { groups, updateCurrentGroup } from "../store/groups.js";

const imagePreview = ref(null);
const imageFileName = ref('');
const imageFile = ref(null);
const tagInput = ref('');
const tags = ref([]);
const errorMsg = ref('');
const eventName = ref('');
const date = ref('');
const description = ref('');
const locationQuery = ref('');
const locationStatus = ref('');
const searchingLocation = ref(false);
const longitude = ref(null);
const latitude = ref(null);
const tagsLimit = ref(10);

const title = 'Create Event';

const handleImageUpload = (event) => {
  const file = event.target.files[0];
  if (file && (file.type === "image/jpeg" || file.type === "image/png")) {
    imagePreview.value = URL.createObjectURL(file);
    imageFileName.value = file.name;
    imageFile.value = file;
    return;
  }

  imagePreview.value = null;
  imageFileName.value = '';
  imageFile.value = null;
  errorMsg.value = 'Only PNG and JPEG images are supported.';
};

const addTag = () => {
  const newTag = tagInput.value.trim();
  if (newTag && !tags.value.includes(newTag) && tags.value.length < tagsLimit.value) {
    tags.value.push(newTag);
    tagInput.value = '';
  }
};

const removeTag = (tag) => {
  tags.value = tags.value.filter((item) => item !== tag);
};

const applyCoordinates = (nextLat, nextLong, label) => {
  latitude.value = Number(nextLat);
  longitude.value = Number(nextLong);
  locationStatus.value = `${label} (${latitude.value.toFixed(4)}, ${longitude.value.toFixed(4)})`;
  errorMsg.value = '';
};

const useCurrentLocation = () => {
  if (!userLocation.tracking) {
    errorMsg.value = 'Enable geolocation in your browser to use your current position.';
    return;
  }
  applyCoordinates(userLocation.location.lat, userLocation.location.lng, 'Using your current location');
};

const resolveLocation = async () => {
  const query = locationQuery.value.trim();
  if (!query) {
    errorMsg.value = 'Enter a location or use your current position.';
    return false;
  }

  searchingLocation.value = true;
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`
    );
    const results = await response.json();
    if (!results.length) {
      errorMsg.value = 'No matching location was found.';
      return false;
    }

    const bestMatch = results[0];
    locationQuery.value = bestMatch.display_name;
    applyCoordinates(bestMatch.lat, bestMatch.lon, 'Pinned location');
    return true;
  } catch (error) {
    errorMsg.value = 'Could not resolve that location right now.';
    return false;
  } finally {
    searchingLocation.value = false;
  }
};

const createEventListner = async () => {
  if (longitude.value == null || latitude.value == null) {
    const resolved = await resolveLocation();
    if (!resolved) {
      return;
    }
  }

  let eventData;
  if (groups.currentGroupIdForEvents == null) {
    eventData = {
      name: eventName.value,
      time: date.value,
      long: longitude.value,
      lat: latitude.value,
      description: description.value,
      tags: tags.value,
      eventCreator: auth.user.username,
      userId: auth.user.userId,
    };
  } else {
    eventData = {
      name: eventName.value,
      time: date.value,
      long: longitude.value,
      lat: latitude.value,
      description: description.value,
      tags: tags.value,
      eventCreator: auth.user.username,
      userId: auth.user.userId,
      groupId: groups.currentGroupIdForEvents,
    };
    updateCurrentGroup(groups.currentGroupIdForEvents);
    groups.currentGroupIdForEvents = null;
  }

  try {
    const fileToUpload = imagePreview.value ? imageFile.value : null;
    const response = await addEvent(eventData, fileToUpload);
    errorMsg.value = !response.result ? response.msg : '';
    if (!response.result) {
      return;
    }

    date.value = '';
    description.value = '';
    eventName.value = '';
    imagePreview.value = null;
    imageFileName.value = '';
    imageFile.value = null;
    tags.value = [];
    tagInput.value = '';
    locationQuery.value = '';
    locationStatus.value = '';
    longitude.value = null;
    latitude.value = null;

    await nextTick();
    pages.dropLayer();
  } catch (error) {
    errorMsg.value = error.message || 'An error occurred while creating the event';
  }
};

function dropLayerandBack() {
  groups.currentGroupIdForEvents = null;
  pages.dropLayer();
}
</script>

<template>
  <Page :title="title">
    <form class="add-event-form" @submit.prevent>
      <div class="image-upload-container">
        <input id="event-image-input" type="file" accept="image/png, image/jpeg" hidden @change="handleImageUpload" />
        <label
          for="event-image-input"
          class="image-upload-label"
          :style="imagePreview ? `background-image: url(${imagePreview})` : ''"
        >
          <div v-if="!imagePreview" class="image-overlay">
            <svg-icon :path="mdiCamera" width="1.5rem" class="icon" />
            <span>Upload Event Image</span>
          </div>
        </label>
        <div v-if="imagePreview" class="image-name">
          <span>{{ imageFileName }}</span>
        </div>
      </div>

      <input v-model="eventName" type="text" placeholder="Event Name" />
      <input v-model="date" type="date" placeholder="Date" />

      <div class="location-section">
        <div class="location-input-row">
          <input
            v-model="locationQuery"
            type="text"
            placeholder="Search for a location"
            :disabled="searchingLocation"
          />
          <button type="button" class="inline-btn primary" @click="resolveLocation">
            <svg-icon :path="mdiMapMarker" width="1.1rem" />
            <span>{{ searchingLocation ? 'Searching...' : 'Find' }}</span>
          </button>
        </div>
        <button type="button" class="inline-btn secondary" @click="useCurrentLocation">
          <svg-icon :path="mdiCrosshairsGps" width="1.1rem" />
          <span>Use Current Location</span>
        </button>
        <p v-if="locationStatus" class="location-status">{{ locationStatus }}</p>
      </div>

      <textarea v-model="description" placeholder="Description"></textarea>

      <div class="tags-input">
        <div class="tags-list">
          <span v-for="(tag, index) in tags" :key="index" class="tag">
            {{ tag }}
            <button class="delete-tag" @click.prevent="removeTag(tag)">x</button>
          </span>
          <input
            v-model="tagInput"
            type="text"
            placeholder="Add a tag"
            class="tag-input-field"
            @keyup.space="addTag"
          />
        </div>
        <div class="tag-instructions">
          Press the spacebar after each tag.
          {{ tagsLimit - tags.length }} tags are remaining
        </div>
        <button type="button" class="remove-all-btn" @click="tags = []">
          Remove All
        </button>
      </div>

      <button class="create-btn" @click="createEventListner">Create Event</button>
      <button class="forget-btn" @click="dropLayerandBack">Forget Event</button>
    </form>

    <div v-if="errorMsg" class="error-popup">
      <div class="error-content">
        <span class="error-icon">⚠️</span>
        <p class="error-message">{{ errorMsg }}</p>
        <button class="error-dismiss-btn" @click="errorMsg = ''">Dismiss</button>
      </div>
    </div>
  </Page>
</template>

<style scoped lang="scss">
#page-wrapper {
  padding: 0rem 1rem 0rem 1rem;
}

#page-title {
  h1 {
    text-align: right;
    margin: -2rem;
  }

  hr {
    opacity: 0.5;
  }
}

.add-event-form {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;

  h2 {
    text-align: center;
  }

  hr {
    margin-top: -1rem;
  }

  .image-upload-container {
    margin-bottom: 1rem;
    text-align: center;
    position: relative;
  }

  .image-upload-label {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background-size: cover;
    background-position: center;
    border-radius: 25px;
    width: 100%;
    height: 150px;
    background-color: #d9d9d9;
    cursor: pointer;
    transition: background-color 0.3s;

    &:hover {
      background-color: #c0c0c0;
    }
  }

  .image-name {
    margin-bottom: -1rem;

    span {
      color: #919191;
    }
  }
}

.location-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.location-input-row {
  display: flex;
  gap: 0.5rem;

  input {
    flex: 1;
  }
}

.inline-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  border: none;
  border-radius: 1rem;
  padding: 0.65rem 0.85rem;
  font-weight: 700;
  box-shadow: 0px 2px 4px 0px rgba(0, 0, 0, 0.2);
}

.inline-btn.primary {
  background-color: #ffc01f;
  color: #2c2c2c;
}

.inline-btn.secondary {
  background-color: #dfefff;
  color: #1651a4;
}

.location-status {
  margin: 0;
  font-size: 0.9rem;
  color: #3a7c3c;
}

.create-btn,
.forget-btn,
.remove-all-btn {
  border: none;
  padding: 0.75rem;
  border-radius: 1.5rem;
  font-weight: 700;
  box-shadow: 0px 2px 4px 0px rgba(0, 0, 0, 0.2);
}

.create-btn {
  background-color: #007bff;
  color: white;
}

.forget-btn {
  background-color: #f0f0f0;
}

.remove-all-btn {
  background-color: #ffe7aa;
}

.error-popup {
  margin-top: 1rem;
}

.error-message {
  color: #b22424;
  font-weight: 700;
}
</style>
