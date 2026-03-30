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
    <form class="add-event-form soft-panel" @submit.prevent>
      <div>
        <p class="eyebrow">Create event</p>
        <h2>Make it easy for people to show up.</h2>
        <p class="section-copy">Set the place, tone, and details clearly so the map preview feels trustworthy at a glance.</p>
      </div>

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

      <label class="field-group">
        <span>Event name</span>
        <input v-model="eventName" class="field" type="text" placeholder="Sunset coffee walk" />
      </label>
      <label class="field-group">
        <span>Date</span>
        <input v-model="date" class="field" type="date" placeholder="Date" />
      </label>

      <div class="location-section">
        <span class="location-label">Location</span>
        <div class="location-input-row">
          <input
            v-model="locationQuery"
            class="field"
            type="text"
            placeholder="Search for a location"
            :disabled="searchingLocation"
          />
          <button type="button" class="btn btn-primary inline-btn" @click="resolveLocation">
            <svg-icon :path="mdiMapMarker" width="1.1rem" />
            <span>{{ searchingLocation ? 'Searching...' : 'Find' }}</span>
          </button>
        </div>
        <button type="button" class="btn btn-secondary inline-btn" @click="useCurrentLocation">
          <svg-icon :path="mdiCrosshairsGps" width="1.1rem" />
          <span>Use Current Location</span>
        </button>
        <p v-if="locationStatus" class="location-status">{{ locationStatus }}</p>
      </div>

      <label class="field-group">
        <span>Description</span>
        <textarea class="textarea" v-model="description" placeholder="Tell people what kind of event this is."></textarea>
      </label>

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
        <button type="button" class="btn btn-ghost remove-all-btn" @click="tags = []">
          Remove All
        </button>
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-primary create-btn" @click="createEventListner">Create Event</button>
        <button type="button" class="btn btn-secondary forget-btn" @click="dropLayerandBack">Cancel</button>
      </div>
    </form>

    <div v-if="errorMsg" class="error-popup soft-panel">
      <p class="error-message">{{ errorMsg }}</p>
      <button class="btn btn-secondary error-dismiss-btn" @click="errorMsg = ''">Dismiss</button>
    </div>
  </Page>
</template>

<style scoped lang="scss">
.add-event-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: var(--radius-lg);

  h2 {
    margin: 0.8rem 0 0.55rem;
    font-family: var(--font-display);
    font-size: clamp(1.7rem, 3vw, 2.3rem);
    letter-spacing: -0.05em;
  }
}

.image-upload-container {
  text-align: center;
}

.image-upload-label {
  display: flex;
  align-items: center;
  justify-content: center;
  background-size: cover;
  background-position: center;
  border-radius: var(--radius-lg);
  width: 100%;
  min-height: 14rem;
  background: linear-gradient(145deg, var(--canvas-strong), var(--surface));
  border: 1px dashed var(--border-strong);
  cursor: pointer;
  transition: transform var(--transition-fast), border-color var(--transition-fast);

  &:hover {
    transform: translateY(-2px);
    border-color: var(--accent);
  }
}

.image-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--ink-soft);
  gap: 0.65rem;
}

.image-name {
  margin-top: 0.75rem;

  span {
    color: var(--ink-muted);
  }
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;

  span {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--ink-soft);
  }
}

.location-section {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.location-label {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink-soft);
}

.location-input-row {
  display: flex;
  gap: 0.65rem;
}

.inline-btn {
  white-space: nowrap;
}

.location-status {
  margin: 0.2rem 0 0;
  color: var(--secondary);
  font-size: 0.9rem;
}

.textarea {
  min-height: 9rem;
  resize: vertical;
}

.tags-input {
  background: var(--surface-strong);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  padding: 0.85rem;
  width: 100%;
  min-height: 9rem;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 0.75rem;
}

.tag {
  display: flex;
  align-items: center;
  background: var(--accent-soft);
  color: var(--accent-strong);
  border-radius: var(--radius-pill);
  padding: 0.45rem 0.75rem;
  font-weight: 700;
}

.delete-tag {
  background-color: transparent;
  border: none;
  margin-left: 0.45rem;
  cursor: pointer;
  color: inherit;
}

.tag-input-field {
  flex-grow: 1;
  border: none;
  outline: none;
  padding: 0.35rem 0.15rem;
  background: transparent;
  color: var(--ink);
}

.tag-instructions {
  font-size: 0.85rem;
  color: var(--ink-muted);
  margin-bottom: 0.75rem;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
}

.error-popup {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.15rem;
  border-radius: var(--radius-md);
}

.error-message {
  margin: 0;
  color: var(--danger);
  font-weight: 700;
}

@media (max-width: 720px) {
  .location-input-row {
    flex-direction: column;
  }

  .form-actions,
  .error-popup {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
