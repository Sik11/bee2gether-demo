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
  getUserGroupEvents
} from "../api.js";
import { auth } from '../store/auth';

const initialState = {
  availableEvents: [],
  eventAttendees: [],
  userEvents: [],
  groupEvents: [],

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
    console.log(events.selected)
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
  }
});

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

  setInterval(() => {
    console.log("polling events");
    const { bottom_left_lat, bottom_left_long, top_right_lat, top_right_long } =
      getBounds(getUserLocation().location, getEvents().radius);
      getMapEvents(bottom_left_long, bottom_left_lat, top_right_long, top_right_lat)
        .then((response) => {
            getEvents().availableEvents = response.events;
        })
  }, 10000);
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
  console.log(`Joining event ${eventID}`);
  console.log(userID);
  try {
    const { result, msg, userId, eventId } = await joinEvent(userID, eventID);
    console.log(result, msg, userId, eventId);
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
