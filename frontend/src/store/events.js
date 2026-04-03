import { reactive, toRefs } from "vue";
import { getUserLocation } from "./userLocation.js";
import {
  getMapEvents,
  getEventAttendees,
  removeJoinEvent,
  searchEvent,
  createEvent,
  joinEvent,
  deleteEvent,
  uploadEventImage,
  attendingEvents,
  getUserGroupEvents,
  getEvent,
  saveEvent as saveEventApi,
  removeSavedEvent as removeSavedEventApi,
  getSavedEvents as getSavedEventsApi,
} from "../api.js";
import { auth } from '../store/auth';
import { pages } from "./pages";
import { updateQueryState } from "./urlState";

const initialState = {
  availableEvents: [],
  eventAttendees: [],
  userEvents: [],
  groupEvents: [],
  savedEvents: [],
  userEventsTotal: 0,
  savedEventsTotal: 0,
  loadingAvailableEvents: false,
  loadingUserEvents: false,
  loadingSavedEvents: false,
  hasLoadedAvailableEvents: false,
  hasLoadedUserEvents: false,
  hasLoadedSavedEvents: false,
  filters: {
    window: "all",
    groupsOnly: false,
    tag: "all",
  },

  selected: {
    name: undefined,
    id: undefined,
    lat: undefined,
    long: undefined,
    description: undefined,
    ongoing: undefined,
    time: undefined,
    userId: undefined,
    username: undefined,
    'eventImg(s)': [],
    tags: [],
    attendees: [
      { userId: '', username: '' }
    ]
  },
  searchResults: [],

  radius: 100000,
  viewportBounds: null,
}

const EVENT_POLL_INTERVAL_MS = 30000;
const ATTENDEE_POLL_INTERVAL_MS = 30000;
const GROUP_EVENT_POLL_INTERVAL_MS = 20000;
const MAP_EVENT_CACHE_MS = 4000;
const USER_EVENT_CACHE_MS = 12000;
const SAVED_EVENT_CACHE_MS = 12000;

function areEventsEquivalent(nextEvents = [], currentEvents = []) {
  if (!Array.isArray(nextEvents) || !Array.isArray(currentEvents)) {
    return false;
  }
  if (nextEvents.length !== currentEvents.length) {
    return false;
  }
  return nextEvents.every((event, index) => {
    const current = currentEvents[index];
    return current
      && current.id === event.id
      && current.time === event.time
      && current.startTime === event.startTime
      && current.endTime === event.endTime
      && (current.attendees?.length || 0) === (event.attendees?.length || 0);
  });
}
// an object containing events this user has access to
export const events = reactive({
  // a list of events the user can see TODO: remove dummy events
  ...initialState,

  selectEvent(event) {
    events.selected = {
      ...event,
      attendees: findEventAttendees(event.id)
    }
  },

  getSelected() {
    return events.selected
  },

  async searchEvent(name) {
    const promise = searchEvent(name)
    promise
      .then(data => {
        console.log(`search results: ${data}`)
        console.log(data)
        events.searchResults = data.events || []
      })
      .catch(err => {
        console.error(err)
      })
    return promise
  },

  async updateAvailableEvents(lat = getUserLocation().location.lat, lng = getUserLocation().location.lng) {
    const { bottom_left_lat, bottom_left_long, top_right_lat, top_right_long } =
      getBounds({ lat, lng }, events.radius);
    return events.updateAvailableEventsForBounds({
      bottomLeftLat: bottom_left_lat,
      bottomLeftLong: bottom_left_long,
      upperRightLat: top_right_lat,
      upperRightLong: top_right_long,
    });
  },

  async updateAvailableEventsForBounds(bounds) {
    const normalizedBounds = normalizeViewportBounds(bounds);
    if (!normalizedBounds) {
      return { result: false, msg: "Viewport bounds are unavailable", events: [] };
    }

    events.viewportBounds = normalizedBounds;
    const nextRequestKey = `${normalizedBounds.bottomLeftLat}:${normalizedBounds.bottomLeftLong}:${normalizedBounds.upperRightLat}:${normalizedBounds.upperRightLong}`;
    const now = Date.now();
    if (
      events._availableEventsRequest
      && events._availableEventsRequest.key === nextRequestKey
    ) {
      return events._availableEventsRequest.promise;
    }

    if (
      events._availableEventsSnapshot?.key === nextRequestKey
      && now - events._availableEventsSnapshot.at < MAP_EVENT_CACHE_MS
    ) {
      return {
        result: true,
        events: events.availableEvents,
        msg: "Using cached map events",
      };
    }

    events.loadingAvailableEvents = true;
    try {
      const requestPromise = getMapEvents(
        normalizedBounds.bottomLeftLong,
        normalizedBounds.bottomLeftLat,
        normalizedBounds.upperRightLong,
        normalizedBounds.upperRightLat
      );
      events._availableEventsRequest = {
        key: nextRequestKey,
        promise: requestPromise,
      };
      const response = await requestPromise;
      const nextEvents = response.events || [];
      if (!areEventsEquivalent(nextEvents, events.availableEvents)) {
        events.availableEvents = nextEvents;
      }
      events._availableEventsSnapshot = {
        key: nextRequestKey,
        at: Date.now(),
      };
      events.hasLoadedAvailableEvents = true;
      return response;
    } catch (error) {
      if (auth.isLoggedIn || pages.selected === 'map') {
        console.error(error);
      }
      return { result: false, msg: error.message, events: [] };
    } finally {
      events.loadingAvailableEvents = false;
      if (events._availableEventsRequest?.key === nextRequestKey) {
        events._availableEventsRequest = null;
      }
    }
  }
});

events.selectEvent = function selectEvent(event, options = {}) {
  const { openLayer = true, syncUrl = true } = options;
  events.selected = {
    ...event,
    attendees: findEventAttendees(event.id)
  };
  if (openLayer && !pages.layers.includes("event-overview")) {
    pages.addLayer("event-overview");
  }
  if (syncUrl) {
    updateQueryState({ event: event?.id ?? null, group: null, tab: pages.selected });
  }
};

events.clearSelectedEvent = function clearSelectedEvent(options = {}) {
  const { syncUrl = true } = options;
  events.selected = { ...initialState.selected };
  if (syncUrl) {
    updateQueryState({ event: null });
  }
};

events.setFilterWindow = function setFilterWindow(value) {
  events.filters.window = value;
};

events.toggleGroupsOnly = function toggleGroupsOnly() {
  events.filters.groupsOnly = !events.filters.groupsOnly;
};

events.setTagFilter = function setTagFilter(value) {
  events.filters.tag = value;
};

events.getAvailableTags = function getAvailableTags() {
  const tags = new Set();
  for (const event of events.availableEvents) {
    for (const tag of event.tags || []) {
      if (tag) {
        tags.add(tag);
      }
    }
  }
  return ["all", ...Array.from(tags).sort((a, b) => a.localeCompare(b))];
};

events.getFilteredAvailableEvents = function getFilteredAvailableEvents() {
  const now = new Date();
  const endOfWeek = new Date(now);
  endOfWeek.setDate(now.getDate() + 7);

  return events.availableEvents.filter((event) => {
    const eventTime = event?.time ? new Date(event.time) : null;
    const inToday = eventTime && eventTime.toDateString() === now.toDateString();
    const inWeek = eventTime && eventTime >= now && eventTime <= endOfWeek;

    if (events.filters.window === "today" && !inToday) {
      return false;
    }
    if (events.filters.window === "week" && !inWeek) {
      return false;
    }
    if (events.filters.groupsOnly && !event.groupId) {
      return false;
    }
    if (events.filters.tag !== "all" && !(event.tags || []).includes(events.filters.tag)) {
      return false;
    }
    return true;
  });
};

events.isEventSaved = function isEventSaved(eventId) {
  return events.savedEvents.some((event) => event.id === eventId);
};

events.selectEventById = async function selectEventById(eventId, options = {}) {
  if (!eventId) {
    return null;
  }

  let event = events.availableEvents.find((entry) => entry.id === eventId)
    || events.userEvents.find((entry) => entry.id === eventId)
    || events.groupEvents.find((entry) => entry.id === eventId)
    || events.savedEvents.find((entry) => entry.id === eventId);
  if (!event) {
    const response = await getEvent(eventId);
    event = response?.event || response?.eventInfo || null;
  }
  if (!event) {
    return null;
  }
  events.selectEvent(event, options);
  return event;
};

export async function updateUserEvents(userId, options = {}) {
  if (!userId) {
    events.userEvents = [];
    events.userEventsTotal = 0;
    events.hasLoadedUserEvents = false;
    return { result: false, msg: 'UserId is required' };
  }

  const offset = Number(options.offset || 0);
  const limit = Number(options.limit || 5);

  const now = Date.now();
  if (
    events._userEventsRequest?.key === `${userId}:${offset}:${limit}`
  ) {
    return events._userEventsRequest.promise;
  }
  if (
    events._userEventsSnapshot?.key === `${userId}:${offset}:${limit}`
    && now - events._userEventsSnapshot.at < USER_EVENT_CACHE_MS
  ) {
    return { result: true, attendingEvents: events.userEvents, msg: 'Using cached user events' };
  }

  events.loadingUserEvents = true;
  try {
    const requestPromise = attendingEvents(userId, { offset, limit });
    events._userEventsRequest = { key: `${userId}:${offset}:${limit}`, promise: requestPromise };
    const response = await requestPromise;
    if (response.result) {
      const nextEvents = response.attendingEvents || [];
      if (!areEventsEquivalent(nextEvents, getEvents().userEvents)) {
        getEvents().userEvents = nextEvents;
      }
      events.userEventsTotal = Number(response.total ?? nextEvents.length);
      events._userEventsSnapshot = { key: `${userId}:${offset}:${limit}`, at: Date.now() };
      events.hasLoadedUserEvents = true;
    } else {
      console.error(response.msg || 'Failed to get user events');
    }
    return response;
  } catch (error) {
    if (auth.isLoggedIn && auth.user?.userId) {
      console.error(error.message);
    }
    return { result: false, msg: error.message };
  } finally {
    events.loadingUserEvents = false;
    if (events._userEventsRequest?.key === `${userId}:${offset}:${limit}`) {
      events._userEventsRequest = null;
    }
  }
}

export async function updateSavedEvents(userId, options = {}) {
  if (!userId) {
    events.savedEvents = [];
    events.savedEventsTotal = 0;
    events.hasLoadedSavedEvents = false;
    return { result: false, msg: 'UserId is required' };
  }

  const offset = Number(options.offset || 0);
  const limit = Number(options.limit || 5);

  const now = Date.now();
  if (events._savedEventsRequest?.key === `${userId}:${offset}:${limit}`) {
    return events._savedEventsRequest.promise;
  }
  if (
    events._savedEventsSnapshot?.key === `${userId}:${offset}:${limit}`
    && now - events._savedEventsSnapshot.at < SAVED_EVENT_CACHE_MS
  ) {
    return { result: true, savedEvents: events.savedEvents, msg: 'Using cached saved events' };
  }
  events.loadingSavedEvents = true;
  try {
    const requestPromise = getSavedEventsApi(userId, { offset, limit });
    events._savedEventsRequest = { key: `${userId}:${offset}:${limit}`, promise: requestPromise };
    const response = await requestPromise;
    if (response.result) {
      const nextEvents = response.savedEvents || [];
      if (!areEventsEquivalent(nextEvents, events.savedEvents)) {
        events.savedEvents = nextEvents;
      }
      events.savedEventsTotal = Number(response.total ?? nextEvents.length);
      events._savedEventsSnapshot = { key: `${userId}:${offset}:${limit}`, at: Date.now() };
      events.hasLoadedSavedEvents = true;
    } else if ((response.msg || '').toLowerCase().includes('user not found')) {
      events.savedEvents = [];
      events.savedEventsTotal = 0;
      await auth.recoverMissingUser();
    }
    return response;
  } catch (error) {
    if (auth.isLoggedIn && auth.user?.userId) {
      console.error(error.message);
    }
    return { result: false, msg: error.message };
  } finally {
    events.loadingSavedEvents = false;
    if (events._savedEventsRequest?.key === `${userId}:${offset}:${limit}`) {
      events._savedEventsRequest = null;
    }
  }
}

export async function preloadPersonalEventData(userId) {
  if (!userId) {
    return;
  }
  await Promise.allSettled([
    updateUserEvents(userId, { limit: 5, offset: 0 }),
    updateSavedEvents(userId, { limit: 5, offset: 0 }),
  ]);
}


function getBounds(position, radius) {
  const lat = position.lat;
  const lng = position.lng;
  const latOffset = radius / 111111;
  const lngOffset = radius / 111111 / Math.cos(lat);
  return {
    bottom_left_lat: (lat - latOffset).toString(),
    bottom_left_long: (lng - lngOffset).toString(),
    top_right_lat: (lat + latOffset).toString(),
    top_right_long: (lng + lngOffset).toString(),
  };
}

function normalizeViewportBounds(bounds) {
  if (!bounds) {
    return null;
  }

  const rawSouth = bounds.bottomLeftLat ?? bounds._sw?.lat ?? bounds.getSouth?.();
  const rawWest = bounds.bottomLeftLong ?? bounds._sw?.lng ?? bounds.getWest?.();
  const rawNorth = bounds.upperRightLat ?? bounds._ne?.lat ?? bounds.getNorth?.();
  const rawEast = bounds.upperRightLong ?? bounds._ne?.lng ?? bounds.getEast?.();

  const south = Number(rawSouth);
  const west = Number(rawWest);
  const north = Number(rawNorth);
  const east = Number(rawEast);

  if (![south, west, north, east].every(Number.isFinite)) {
    return null;
  }

  return {
    bottomLeftLat: south.toString(),
    bottomLeftLong: west.toString(),
    upperRightLat: north.toString(),
    upperRightLong: east.toString(),
  };
}

function hasUsableLocation(position) {
  return Number.isFinite(position?.lat)
    && Number.isFinite(position?.lng)
    && (position.lat !== 0 || position.lng !== 0);
}

function isDocumentHidden() {
  return typeof document !== 'undefined' && document.hidden;
}

let eventPollingStarted = false;
let eventPollInFlight = false;
let attendeePollingStarted = false;
let attendeePollInFlight = false;
let groupEventPollingStarted = false;
let groupEventPollInFlight = false;

// start polling for events
export function startPollingEvents() {
  if (eventPollingStarted) {
    return;
  }
  eventPollingStarted = true;

  const pollEvents = async () => {
    if (eventPollInFlight) {
      setTimeout(pollEvents, EVENT_POLL_INTERVAL_MS);
      return;
    }

    if (pages.selected !== 'map') {
      setTimeout(pollEvents, EVENT_POLL_INTERVAL_MS);
      return;
    }

    if (isDocumentHidden()) {
      setTimeout(pollEvents, EVENT_POLL_INTERVAL_MS);
      return;
    }

    if (!events.viewportBounds) {
      setTimeout(pollEvents, EVENT_POLL_INTERVAL_MS);
      return;
    }

    eventPollInFlight = true;
    try {
      await getEvents().updateAvailableEventsForBounds(events.viewportBounds);
    } finally {
      eventPollInFlight = false;
      setTimeout(pollEvents, EVENT_POLL_INTERVAL_MS);
    }
  };

  pollEvents();
}

export function startPollingEventAttendees() {
  if (attendeePollingStarted) {
    return;
  }
  attendeePollingStarted = true;

  const pollAttendees = async () => {
    if (attendeePollInFlight) {
      setTimeout(pollAttendees, ATTENDEE_POLL_INTERVAL_MS);
      return;
    }

    if (!['events', 'groups'].includes(pages.selected)) {
      setTimeout(pollAttendees, ATTENDEE_POLL_INTERVAL_MS);
      return;
    }

    if (isDocumentHidden()) {
      setTimeout(pollAttendees, ATTENDEE_POLL_INTERVAL_MS);
      return;
    }

    attendeePollInFlight = true;
    try {
      const response = await getEventAttendees();
      getEvents().eventAttendees = response.eventAttendees;
    } catch (error) {
      console.error(error);
    } finally {
      attendeePollInFlight = false;
      setTimeout(pollAttendees, ATTENDEE_POLL_INTERVAL_MS);
    }
  };

  pollAttendees();
}


// startinig polling group events:
export function startPollingGroupEvents() {
  if (groupEventPollingStarted) {
    return;
  }
  groupEventPollingStarted = true;

  const pollGroupEvents = async () => {
    if (groupEventPollInFlight) {
      setTimeout(pollGroupEvents, GROUP_EVENT_POLL_INTERVAL_MS);
      return;
    }

    if (!auth.isLoggedIn || !auth.user?.userId) {
      setTimeout(pollGroupEvents, GROUP_EVENT_POLL_INTERVAL_MS);
      return;
    }

    if (isDocumentHidden()) {
      setTimeout(pollGroupEvents, GROUP_EVENT_POLL_INTERVAL_MS);
      return;
    }

    groupEventPollInFlight = true;
    try {
      const response = await getUserGroupEvents(auth.user.userId);
      getEvents().groupEvents = response.events;
    } catch (error) {
      console.error(error);
    } finally {
      groupEventPollInFlight = false;
      setTimeout(pollGroupEvents, GROUP_EVENT_POLL_INTERVAL_MS);
    }
  };

  pollGroupEvents();
}

// get ref to events
export function getEvents() {
  return events;
}

export function resetEventsState() {
  events.availableEvents = [];
  events.eventAttendees = [];
  events.userEvents = [];
  events.userEventsTotal = 0;
  events.groupEvents = [];
  events.savedEvents = [];
  events.savedEventsTotal = 0;
  events.loadingAvailableEvents = false;
  events.loadingUserEvents = false;
  events.loadingSavedEvents = false;
  events.hasLoadedAvailableEvents = false;
  events.hasLoadedUserEvents = false;
  events.hasLoadedSavedEvents = false;
  events.viewportBounds = null;
  events._availableEventsRequest = null;
  events._availableEventsSnapshot = null;
  events._userEventsRequest = null;
  events._userEventsSnapshot = null;
  events._savedEventsRequest = null;
  events._savedEventsSnapshot = null;
}

export function findEventAttendees(eventId) {
  const foundEvent = events.eventAttendees.find(
    (event) => event.eventId === eventId
  );
  return foundEvent ? foundEvent.attendees : [];
}

/**
 * @param {Object} eventData 
 * @return {Promise<{result: boolean, msg: string, eventId?: string}>}
 */
export async function addEvent(eventData, imageFile) {
  try {
    const { result, msg, eventId } = await createEvent(eventData);
    if (result && eventId) {
      const newEvent = {
        ...eventData,
        id: eventId
      };
      getEvents().availableEvents.push(newEvent);
      if (imageFile) {
        const imageResponse = await uploadEventImage(imageFile, eventId);
        console.log(imageResponse);
        if (!imageResponse.result) {
          return { result: false, msg: imageResponse.msg || 'Failed to upload event image.' };
        }
      }
      await updateUserEvents(eventData.userId);
      await updateSavedEvents(eventData.userId);

      const eventAttendees = {
        eventId: eventId,
        attendees: [{ "userId": eventData.userId, "username": eventData.eventCreator }]
      };
      getEvents().eventAttendees.push(eventAttendees);

      return { result, msg };
    } else {
      return { result: false, msg: msg || 'Event creation failed' };
    }
  } catch (error) {
    console.error(error);
    return { result: false, msg: error.message };
  }
}

export async function removeEvent(eventID, userID) {
  try {
    const { result, msg } = await deleteEvent(eventID, userID);
    console.log(result);
    console.log(msg);
    if (result) {
      getEvents().availableEvents = getEvents().availableEvents.filter(
        (event) => event.id !== eventID
      );
      await updateUserEvents(userID);
      await updateSavedEvents(userID);
      return { result, msg };
    } else {
      return { result: false, msg: msg || "Event deletion failed" };
    }
  } catch (error) {
    console.error(error);
    return { result: false, msg: error.message };
  }
}

export async function sendJoinEvent(userID, username, eventID) {
  try {
    const { result, msg, userId, eventId } = await joinEvent(userID, eventID);
    if (result && userId && eventId) {
      const foundEventIndex = getEvents().eventAttendees.findIndex(
        (event) => event.eventId === eventId
      );

      if (foundEventIndex !== -1) {
        getEvents().eventAttendees[foundEventIndex].attendees.push({
          userId: userId,
          username: username,
        });
      } else {
        // Event not found: Add a new event
        const newEventObject = {
          eventId: eventId,
          attendees: [{ userId: userId, username: username }],
        };
        getEvents().eventAttendees.push(newEventObject);
      }
      console.log(`Successfully joined event ${eventId}`);
      await updateUserEvents(userID);
      await updateSavedEvents(userID);
      return { result, msg };
    } else {
      console.log(`Failed to join event ${eventId}`);
      return { result: false, msg: msg || "Failed to join event" };
    }
  } catch (err) {
    console.error(err);
    return { result: false, msg: err.message };
  }
}

export async function sendLeaveEvent(userID, eventID) {
  console.log(`Leaving event ${eventID}`);
  try {
    const { result, msg, userId, eventId } = await removeJoinEvent(
      userID,
      eventID
    );
    if (result && userId && eventId) {
      const events = getEvents();
      const foundEventIndex = events.eventAttendees.findIndex(
        (event) => event.eventId === eventId
      );

      if (foundEventIndex !== -1) {
        const foundEvent = events.eventAttendees[foundEventIndex];
        const foundUserIndex = foundEvent.attendees.findIndex(
          (user) => user.userId === userId
        );

        if (foundUserIndex !== -1) {
          foundEvent.attendees.splice(foundUserIndex, 1);
        }
      }

      console.log(`Successfully left event ${eventId}`);
      await updateUserEvents(userID);
      await updateSavedEvents(userID);
      return { result, msg };
    } else {
      console.log(`Failed to leave event ${eventId}`);
      return { result: false, msg: msg || "Failed to leave event" };
    }
  } catch (err) {
    console.error(err);
    return { result: false, msg: err.message };
  }
}

export async function toggleSavedEvent(userId, eventId) {
  try {
    const response = events.isEventSaved(eventId)
      ? await removeSavedEventApi(userId, eventId)
      : await saveEventApi(userId, eventId);
    if (response.result) {
      await updateSavedEvents(userId);
    }
    return response;
  } catch (error) {
    console.error(error);
    return { result: false, msg: error.message };
  }
}
