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

    try {
      const response = await getMapEvents(bottom_left_long, bottom_left_lat, top_right_long, top_right_lat);
      events.availableEvents = response.events || [];
      return response;
    } catch (error) {
      console.error(error);
      return { result: false, msg: error.message, events: [] };
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

export async function updateUserEvents(userId) {
  try {
    const response = await attendingEvents(userId);
    console.log(response.result);
    console.log(response.attendingEvents);
    if (response.result) {
      getEvents().userEvents = response.attendingEvents;
    } else {
      console.error(response.msg || 'Failed to get user events');
    }
  } catch (error) {
    console.error(error.message);
  }
}

export async function updateSavedEvents(userId) {
  if (!userId) {
    events.savedEvents = [];
    return { result: false, msg: 'UserId is required' };
  }
  try {
    const response = await getSavedEventsApi(userId);
    if (response.result) {
      events.savedEvents = response.savedEvents || [];
    } else if ((response.msg || '').toLowerCase().includes('user not found')) {
      events.savedEvents = [];
      await auth.recoverMissingUser();
    }
    return response;
  } catch (error) {
    console.error(error.message);
    return { result: false, msg: error.message };
  }
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

function hasUsableLocation(position) {
  return Number.isFinite(position?.lat)
    && Number.isFinite(position?.lng)
    && (position.lat !== 0 || position.lng !== 0);
}

// track if polling is already happening
let polling = false;

// start polling for events
export function startPollingEvents() {
  console.log("trying polling events");
  if (polling) {
    console.log("already polling events");
    return;
  }
  console.log("starting polling events");
  polling = true;

  const pollEvents = () => {
    const currentLocation = getUserLocation().location;
    if (!hasUsableLocation(currentLocation)) {
      return;
    }

    getEvents().updateAvailableEvents(currentLocation.lat, currentLocation.lng);
  };

  pollEvents();
  setInterval(pollEvents, 10000);
}

export function startPollingEventAttendees() {
  getEventAttendees()
    .then((response) => {
      getEvents().eventAttendees = response.eventAttendees;
    })
    .then(() => {
      setTimeout(startPollingEventAttendees, 10000);
    });
}


// startinig polling group events:
export function startPollingGroupEvents() {
  getUserGroupEvents(auth.user.userId)
    .then((response) => {
      getEvents().groupEvents = response.events;
    })
    .then(() => {
      setTimeout(startPollingGroupEvents, 10000);
    });
}

// get ref to events
export function getEvents() {
  return events;
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
