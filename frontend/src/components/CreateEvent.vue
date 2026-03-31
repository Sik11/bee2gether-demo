<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import { mdiCamera, mdiClose, mdiCrosshairsGps, mdiMagnify, mdiMapMarkerRadiusOutline, mdiRefresh } from '@mdi/js';
import EventSheetMap from './helper/EventSheetMap.vue';
import svgIcon from './helper/svg-icon.vue';
import { userLocation } from '../store/userLocation.js';
import { pages } from '../store/pages';
import { auth } from '../store/auth';
import { addEvent } from '../store/events.js';
import { groups, updateCurrentGroup } from '../store/groups.js';
import { settings } from '../store/settings';
import logo from '../assets/logo.png';
import darkLogo from '../assets/dark-logo.png';

const imagePreview = ref(null);
const imageFileName = ref('');
const imageFile = ref(null);
const tagInput = ref('');
const tags = ref([]);
const errorMsg = ref('');
const eventName = ref('');
const date = ref('');
const startClock = ref('18:00');
const endClock = ref('20:00');
const description = ref('');
const locationQuery = ref('');
const locationStatus = ref('');
const searchingLocation = ref(false);
const locationSuggestions = ref([]);
const showSuggestions = ref(false);
const longitude = ref(null);
const latitude = ref(null);
const tagsLimit = ref(10);
let locationSearchToken = 0;
let suggestionTimeoutId = null;

const activeLogo = computed(() => (settings.isDarkMode ? darkLogo : logo));
const selectedPlaceTitle = computed(() => {
  const query = locationQuery.value.trim();
  if (query) {
    return query.split(',')[0];
  }
  if (Number.isFinite(latitude.value) && Number.isFinite(longitude.value)) {
    return 'Pinned location';
  }
  return 'Choose a place';
});
const selectedPlaceSubtitle = computed(() => {
  if (locationStatus.value) {
    return locationStatus.value;
  }
  if (Number.isFinite(latitude.value) && Number.isFinite(longitude.value)) {
    return `${latitude.value.toFixed(4)}, ${longitude.value.toFixed(4)}`;
  }
  return 'Search on the right or use your current location';
});

const buildEventTimes = () => {
  if (!date.value) {
    throw new Error('Select a date for the event.');
  }
  if (!startClock.value || !endClock.value) {
    throw new Error('Select both a start and end time.');
  }

  const start = new Date(`${date.value}T${startClock.value}`);
  const end = new Date(`${date.value}T${endClock.value}`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    throw new Error('Enter valid start and end times.');
  }
  if (end <= start) {
    throw new Error('End time must be later than the start time.');
  }

  return {
    startTime: start.toISOString(),
    endTime: end.toISOString(),
  };
};

const handleImageUpload = (event) => {
  const file = event.target.files[0];
  if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
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

const applyCoordinates = (nextLat, nextLong, label, details = {}) => {
  latitude.value = Number(nextLat);
  longitude.value = Number(nextLong);
  if (details.placeName) {
    locationQuery.value = details.placeName;
  }
  locationStatus.value = details.address || `${label} (${latitude.value.toFixed(4)}, ${longitude.value.toFixed(4)})`;
  locationSuggestions.value = [];
  showSuggestions.value = false;
  errorMsg.value = '';
};

const useCurrentLocation = () => {
  if (!userLocation.tracking) {
    errorMsg.value = 'Enable geolocation in your browser to use your current position.';
    return;
  }
  applyCoordinates(userLocation.location.lat, userLocation.location.lng, 'Using your current location');
};

async function fetchLocationSuggestions(query) {
  const nextQuery = query.trim();
  if (nextQuery.length < 2) {
    locationSuggestions.value = [];
    showSuggestions.value = false;
    return;
  }

  const token = ++locationSearchToken;
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&addressdetails=1&q=${encodeURIComponent(nextQuery)}`
    );
    const results = await response.json();
    if (token !== locationSearchToken) {
      return;
    }
    locationSuggestions.value = results.map((result) => ({
      id: result.place_id,
      title: result.display_name.split(',')[0],
      subtitle: result.display_name,
      lat: Number(result.lat),
      lng: Number(result.lon),
    }));
    showSuggestions.value = locationSuggestions.value.length > 0;
  } catch (_error) {
    if (token === locationSearchToken) {
      locationSuggestions.value = [];
      showSuggestions.value = false;
    }
  }
}

const resolveLocation = async (queryOverride = null) => {
  const query = (queryOverride ?? locationQuery.value).trim();
  if (!query) {
    errorMsg.value = 'Enter a location or use your current position.';
    return false;
  }

  searchingLocation.value = true;
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&addressdetails=1&q=${encodeURIComponent(query)}`
    );
    const results = await response.json();
    if (!results.length) {
      errorMsg.value = 'No matching location was found.';
      return false;
    }

    const bestMatch = results[0];
    applyCoordinates(bestMatch.lat, bestMatch.lon, 'Pinned location', {
      placeName: bestMatch.display_name.split(',')[0],
      address: bestMatch.display_name,
    });
    return true;
  } catch (error) {
    errorMsg.value = 'Could not resolve that location right now.';
    return false;
  } finally {
    searchingLocation.value = false;
  }
};

function selectMapCoordinates({ lat, lng }) {
  applyCoordinates(lat, lng, 'Pinned from map');
}

function selectSuggestion(suggestion) {
  applyCoordinates(suggestion.lat, suggestion.lng, 'Pinned location', {
    placeName: suggestion.title,
    address: suggestion.subtitle,
  });
}

const createEventListner = async () => {
  let times;
  try {
    times = buildEventTimes();
  } catch (error) {
    errorMsg.value = error.message;
    return;
  }

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
      time: times.startTime,
      startTime: times.startTime,
      endTime: times.endTime,
      long: longitude.value,
      lat: latitude.value,
      description: description.value,
      tags: tags.value,
      eventCreator: auth.user.username,
      userId: auth.user.userId,
      placeName: selectedPlaceTitle.value,
      placeAddress: locationStatus.value || selectedPlaceSubtitle.value,
    };
  } else {
    eventData = {
      name: eventName.value,
      time: times.startTime,
      startTime: times.startTime,
      endTime: times.endTime,
      long: longitude.value,
      lat: latitude.value,
      description: description.value,
      tags: tags.value,
      eventCreator: auth.user.username,
      userId: auth.user.userId,
      groupId: groups.currentGroupIdForEvents,
      placeName: selectedPlaceTitle.value,
      placeAddress: locationStatus.value || selectedPlaceSubtitle.value,
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
    startClock.value = '18:00';
    endClock.value = '20:00';
    description.value = '';
    eventName.value = '';
    imagePreview.value = null;
    imageFileName.value = '';
    imageFile.value = null;
    tags.value = [];
    tagInput.value = '';
    locationQuery.value = '';
    locationStatus.value = '';
    locationSuggestions.value = [];
    showSuggestions.value = false;
    longitude.value = null;
    latitude.value = null;

    await nextTick();
    pages.dropLayer();
  } catch (error) {
    errorMsg.value = error.message || 'An error occurred while creating the event';
  }
};

function closeSheet() {
  groups.currentGroupIdForEvents = null;
  pages.dropLayer();
}

watch(locationQuery, (value) => {
  if (suggestionTimeoutId) {
    window.clearTimeout(suggestionTimeoutId);
  }
  suggestionTimeoutId = window.setTimeout(() => {
    fetchLocationSuggestions(value);
  }, 220);
});
</script>

<template>
  <section class="event-sheet soft-panel event-sheet--create">
    <header class="event-sheet__header">
      <div class="event-sheet__identity">
        <img :src="activeLogo" alt="Bee2Gether logo" />
        <span>Bee2Gether</span>
        <span class="event-sheet__divider"></span>
        <strong>Create event</strong>
      </div>
      <button type="button" class="event-sheet__icon-btn" aria-label="Close create event" @click="closeSheet">
        <svg-icon :path="mdiClose" width="1.1rem" height="1.1rem" />
      </button>
    </header>

    <div class="event-sheet__body">
      <section class="event-sheet__main">
        <div class="event-sheet__intro">
          <h2>Create an event</h2>
          <p>Set the vibe, place, and time so people can say yes quickly.</p>
        </div>

        <section class="editor-section">
          <h3>Basics</h3>

          <label class="field-group">
            <span>Event name</span>
            <input v-model="eventName" class="field" type="text" placeholder="Sunset coffee walk" />
          </label>

          <label class="field-group">
            <span>Description</span>
            <textarea v-model="description" class="textarea" placeholder="Add a short description people can scan fast."></textarea>
          </label>

          <div class="editor-row editor-row--schedule">
            <label class="field-group">
              <span>Date</span>
              <input v-model="date" class="field" type="date" />
            </label>

            <label class="field-group">
              <span>Start time</span>
              <input v-model="startClock" class="field" type="time" />
            </label>

            <label class="field-group">
              <span>End time</span>
              <input v-model="endClock" class="field" type="time" />
            </label>
          </div>

          <div class="field-group">
            <span>Cover image</span>
            <input id="event-image-input" type="file" accept="image/png, image/jpeg" hidden @change="handleImageUpload" />
            <label
              for="event-image-input"
              class="image-upload-label"
              :style="imagePreview ? `background-image: url(${imagePreview})` : ''"
            >
              <div v-if="!imagePreview" class="image-overlay">
                <svg-icon :path="mdiCamera" width="1.2rem" height="1.2rem" />
                <span>Upload cover image</span>
                <small>PNG or JPEG</small>
              </div>
            </label>
            <p v-if="imagePreview" class="image-name">{{ imageFileName }}</p>
          </div>

          <div class="field-group">
            <span>Tags</span>
            <div class="tags-input">
              <div class="tags-list">
                <span v-for="(tag, index) in tags" :key="index" class="tag">
                  {{ tag }}
                  <button class="delete-tag" @click.prevent="removeTag(tag)">x</button>
                </span>
                <input
                  v-model="tagInput"
                  type="text"
                  placeholder="Add tags"
                  class="tag-input-field"
                  @keyup.space="addTag"
                />
              </div>
              <div class="tag-instructions">Press space after each tag. {{ tagsLimit - tags.length }} tags remaining.</div>
            </div>
          </div>

          <p v-if="errorMsg" class="error-inline">{{ errorMsg }}</p>
        </section>
      </section>

      <aside class="event-sheet__side">
        <div class="side-pane">
          <div class="side-pane__toolbar">
            <div class="location-search-stack">
              <div class="location-search-row">
                <label class="location-search">
                  <svg-icon :path="mdiMagnify" width="1rem" height="1rem" />
                  <input
                    v-model="locationQuery"
                    type="text"
                    placeholder="Search location"
                    :disabled="searchingLocation"
                    @focus="showSuggestions = locationSuggestions.length > 0"
                    @keydown.enter.prevent="locationSuggestions[0] ? selectSuggestion(locationSuggestions[0]) : resolveLocation()"
                  />
                </label>
                <button type="button" class="location-refresh" aria-label="Search location" @click="resolveLocation()">
                  <svg-icon :path="mdiRefresh" width="0.95rem" height="0.95rem" />
                </button>
              </div>
              <div v-if="showSuggestions && locationSuggestions.length" class="location-suggestions soft-panel">
                <button
                  v-for="suggestion in locationSuggestions"
                  :key="suggestion.id"
                  type="button"
                  class="location-suggestion"
                  @click="selectSuggestion(suggestion)"
                >
                  <strong>{{ suggestion.title }}</strong>
                  <span>{{ suggestion.subtitle }}</span>
                </button>
              </div>
            </div>
          </div>

          <button type="button" class="location-chip" @click="useCurrentLocation">
            <svg-icon :path="mdiMapMarkerRadiusOutline" width="0.95rem" height="0.95rem" />
            <span>Use current location</span>
          </button>

          <EventSheetMap
            :coordinates="{ lat: latitude, lng: longitude }"
            :user-coordinates="userLocation.location"
            :summary-title="selectedPlaceTitle"
            :summary-subtitle="selectedPlaceSubtitle"
            interactive
            @select-coordinates="selectMapCoordinates"
          />
        </div>
      </aside>
    </div>

    <footer class="event-sheet__footer">
      <button type="button" class="btn btn-secondary" @click="closeSheet">Cancel</button>
      <button type="button" class="btn btn-primary" @click="createEventListner">Create event</button>
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
  border-radius: calc(var(--radius-lg) + 0.25rem);
  border: 1px solid color-mix(in srgb, var(--border-strong) 84%, transparent);
  background: color-mix(in srgb, var(--surface) 96%, transparent);
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
  padding: 0.95rem 1.15rem;
}

.event-sheet__header {
  border-bottom: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
}

.event-sheet__footer {
  justify-content: flex-end;
  border-top: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
  background: color-mix(in srgb, var(--surface) 98%, transparent);
  padding-block: 1.1rem;
  padding-inline: 1.35rem;
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
  grid-template-columns: minmax(0, 1.5fr) minmax(22rem, 0.9fr);
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

.event-sheet__intro {
  display: grid;
  gap: 0.4rem;
  margin-bottom: 1.35rem;

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
    font-size: 1rem;
  }
}

.editor-section {
  display: grid;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.12rem;
  }
}

.field-group {
  display: grid;
  gap: 0.5rem;

  span {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--ink-soft);
  }
}

.editor-row {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(15rem, 0.95fr);
  gap: 1rem;
  align-items: start;
}

.editor-row--schedule {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.image-upload-label {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 10.8rem;
  border-radius: 1.2rem;
  background: linear-gradient(145deg, var(--canvas-strong), var(--surface));
  background-size: cover;
  background-position: center;
  border: 1px dashed color-mix(in srgb, var(--border-strong) 94%, transparent);
  cursor: pointer;
}

.image-overlay {
  display: grid;
  gap: 0.28rem;
  justify-items: center;
  color: var(--ink-soft);

  small {
    color: var(--ink-muted);
  }
}

.image-name {
  margin: 0.45rem 0 0;
  color: var(--ink-muted);
  font-size: 0.85rem;
}

.side-pane {
  height: 100%;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 0.85rem;
}

.side-pane__toolbar {
  display: block;
  padding: 0;
}

.location-search-stack {
  position: relative;
}

.location-search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
}

.location-search {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.88rem 0.95rem;
  border-radius: 1rem 0 0 1rem;
  background: color-mix(in srgb, var(--surface) 96%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  border-right: none;
  color: var(--ink-muted);

  input {
    flex: 1;
    min-width: 0;
    background: transparent;
    color: var(--ink);
    border: none;
    outline: none;
    font: inherit;
  }
}

.location-refresh {
  width: 3.2rem;
  border-radius: 0 1rem 1rem 0;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  background: color-mix(in srgb, var(--surface) 96%, transparent);
  color: var(--ink-soft);
}

.location-suggestions {
  position: absolute;
  top: calc(100% + 0.45rem);
  left: 0;
  right: 0;
  z-index: 8;
  padding: 0.45rem;
  border-radius: 1rem;
  background: color-mix(in srgb, var(--surface) 98%, transparent);
  box-shadow: 0 18px 30px rgba(20, 16, 11, 0.12);
}

.location-suggestion {
  width: 100%;
  display: grid;
  gap: 0.18rem;
  text-align: left;
  padding: 0.7rem 0.8rem;
  border-radius: 0.8rem;
  background: transparent;
  color: var(--ink);
}

.location-suggestion:hover {
  background: color-mix(in srgb, var(--accent-soft) 44%, transparent);
}

.location-suggestion span {
  color: var(--ink-muted);
  font-size: 0.78rem;
  line-height: 1.35;
}

.location-chip {
  width: 100%;
  margin: 0;
  padding: 0.8rem 1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  background: color-mix(in srgb, var(--surface) 96%, transparent);
  color: var(--ink);
  font-weight: 700;
}

.tags-input {
  display: grid;
  gap: 0.55rem;
  padding: 0.9rem 1rem;
  border-radius: 1.1rem;
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  background: color-mix(in srgb, var(--surface) 90%, transparent);
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.42rem 0.7rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--accent-strong);
  font-weight: 700;
}

.delete-tag {
  border: none;
  background: transparent;
  color: inherit;
  font-weight: 700;
  cursor: pointer;
}

.tag-input-field {
  flex: 1;
  min-width: 8rem;
  border: none;
  outline: none;
  background: transparent;
  color: var(--ink);
  font: inherit;
}

.tag-instructions {
  color: var(--ink-muted);
  font-size: 0.82rem;
}

.error-inline {
  margin: 0;
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

  .side-pane {
    grid-template-rows: auto auto 18rem;
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
    padding-inline: 0.9rem;
  }

  .event-sheet__main {
    padding: 1rem 1rem 0;
  }

  .event-sheet__side {
    padding: 0.9rem;
  }

  .editor-row {
    grid-template-columns: 1fr;
  }

  .side-pane__toolbar {
    padding: 0;
  }

  .location-chip {
    width: 100%;
  }
}
</style>
