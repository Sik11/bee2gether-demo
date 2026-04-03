// DICEBEAR API
import { createAvatar } from '@dicebear/core';
import { lorelei, funEmoji } from '@dicebear/collection';

/**
 * Get the avatar for that username (is username specific)
 * @param {*} name 
 * @returns 
 */
export const getAvatar = (name) => createAvatar(lorelei, {
  seed: name,
  scale: 100,
  backgroundColor: ["b6e3f4","c0aede","d1d4f9", "ffd5dc", "ffdfbf"],
  backgroundType: ["solid"], // Removed "gradientLinear" not loading on EventOverview
  backgroundRotation: [0,360],
  earrings: ["variant01","variant02","variant03"],
  earringsProbability: 50
})

// TO OUR API
const API_ENDPOINT = import.meta.env.VITE_API_BASE_URL || "/api";
const CODE = import.meta.env.VITE_API_CODE || "local-demo";
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 0);
const READ_RESPONSE_CACHE_MS = 2500;
const READ_ENDPOINTS = new Set([
  'getAttendingEvents',
  'getEventInfo',
  'getEventComments',
  'getMapEvents',
  'getAllGroups',
  'getAllUserGroups',
  'getGroupEvents',
  'getGroupChatMessages',
  'getSavedEvents',
  'getNotifications',
  'getAllUserGroupEvents',
  'getEventImgs',
]);
const inFlightReadRequests = new Map();
const cachedReadResponses = new Map();

/**
 * Get the string url for that path with client Id.
 * @param {string} path - The commands path.
 * @param {string} clientId - The id of the user making the request, defaults to 'default'.
 * @returns {URL} A URL object to make a request to.
 */
const getUrl = (path, clientId = "default") => {
  const apiRoot = API_ENDPOINT.startsWith("http")
    ? API_ENDPOINT
    : new URL(API_ENDPOINT, window.location.origin).toString();
  const url = new URL(`${path}`, apiRoot.endsWith("/") ? apiRoot : `${apiRoot}/`);
  url.searchParams.set("code", CODE);
  url.searchParams.set("clientId", clientId);
  return url;
};

/**
 * Helper function to create a request function.
 * @param {string} path - The path for the request.
 * @param {string} method - The HTTP method for the request.
 * @param {Object} requestBody - The request body as an object.
 * @returns {function} A function that makes the request.
 */
const createRequestFunction = (path, method, requestBody=undefined) => async () => {
  const isDedupableRead = READ_ENDPOINTS.has(path);
  const requestKey = isDedupableRead
    ? `${method}:${path}:${JSON.stringify(requestBody || {})}`
    : null;
  const now = Date.now();

  if (requestKey && inFlightReadRequests.has(requestKey)) {
    return inFlightReadRequests.get(requestKey);
  }

  if (requestKey) {
    const cached = cachedReadResponses.get(requestKey);
    if (cached && now - cached.at < READ_RESPONSE_CACHE_MS) {
      return cached.data;
    }
  }

  const url = getUrl(path);
  if (method === 'GET' && requestBody && typeof requestBody === 'object') {
    Object.entries(requestBody).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const requestPromise = new Promise((resolve, reject) => {
    const controller = API_TIMEOUT_MS > 0 ? new AbortController() : null;
    const timeoutId = controller
      ? window.setTimeout(() => controller.abort(), API_TIMEOUT_MS)
      : null;

    fetch(url.toString(), {
      method,
      ...(method === 'GET' ? {} : { body: JSON.stringify(requestBody) }),
      headers: {
        'Content-Type': 'application/json',
      },
      ...(controller ? { signal: controller.signal } : {}),
    })
      .then((response) => response.json())
      .then((data) => {
        if (requestKey) {
          cachedReadResponses.set(requestKey, { data, at: Date.now() });
        }
        resolve(data);
      })
      .catch((error) => reject(error))
      .finally(() => {
        if (requestKey) {
          inFlightReadRequests.delete(requestKey);
        }
        if (timeoutId) {
          window.clearTimeout(timeoutId);
        }
      });
  });

  if (requestKey) {
    inFlightReadRequests.set(requestKey, requestPromise);
  }

  return requestPromise;
};

/**
 * Request to create a user.
 * @param {string} username
 * @param {string} password
 * @return {Promise<{result: boolean, msg: string, userId?: string}>}
 */
export const createUser = async (username, password) => 
  createRequestFunction('createUser', 'PUT', {username, password})()

/**
 * Request to login a user.
 * @param {string} username
 * @param {string} password
 * @return {Promise<{result: boolean, msg: string, userId?: string}>}
 */
export const loginUser = async (username, password) => 
  createRequestFunction('loginUser', 'POST', {username, password})()

/**
 * Continue as a browser-scoped guest user.
 * @param {string} guestSessionId
 * @return {Promise<{result: boolean, msg: string, userId?: string, username?: string, isGuest?: boolean}>}
 */
export const continueAsGuest = async (guestSessionId) =>
  createRequestFunction('continueAsGuest', 'POST', { guestSessionId })()


/**
 * Add join user to event
 * @param {string} userId
 * @param {string} eventId
 * @return {Promise<{result: boolean, msg: string, userId: string, eventId: string}>}
 */
export const joinEvent = async (userId, eventId) => 
  createRequestFunction('addAttendingEvent', 'PUT', {userId, eventId})()

/**
 * Remove join user to event
 * @param {string} userId
 * @param {string} eventId
 * @return {Promise<{result: boolean, msg: string, userId: string, eventId: string}>}
 */
export const removeJoinEvent = async (userId, eventId) => 
  createRequestFunction('removeAttendingEvent', 'DELETE', {userId, eventId})()

/**
 * Users attending events
 * @param {string} userId
 * @return {Promise<{result: boolean, msg: string, userId: string, attendingEvents: {EventObjects}}}>}
 */
export const attendingEvents = async (userId, options = {}) => 
  createRequestFunction('getAttendingEvents', 'POST', {userId, ...options})()

  /**
   * Create an event
   * @param {Object} eventData
   * @return {Promise<{result: boolean, msg: string, eventId: string}>}
   */
export const createEvent = async (eventData) =>
    createRequestFunction('createEvent', 'PUT', eventData)()
  

/**
 * Get event info
 * @param {string} eventId
 * @return {Promise<{result: boolean, msg: string, event: {EventObject}}>}
 */
export const getEvent = async (eventId) => 
  createRequestFunction('getEventInfo', 'POST', {eventId})()

export const getEventComments = async (eventId) =>
  createRequestFunction('getEventComments', 'POST', { eventId })()

export const addEventComment = async (eventId, userId, body) =>
  createRequestFunction('addEventComment', 'POST', { eventId, userId, body })()

export const deleteEventComment = async (eventId, commentId, userId) =>
  createRequestFunction('deleteEventComment', 'DELETE', { eventId, commentId, userId })()


/**
 * Get map events
 * @param {string} bottomLeftLong
 * @param {string} bottomLeftLat
 * @param {string} topRightLong
 * @param {string} topRightLat
 * @return {Promise<{result: boolean, events: {EventObjects}}>}
 */
export const getMapEvents = async (bottomLeftLong, bottomLeftLat, upperRightLong, upperRightLat) =>
  createRequestFunction('getMapEvents', 'POST', {bottomLeftLong, bottomLeftLat, upperRightLong, upperRightLat})()

/** 
 * create a group
 * @param {string} name
 * @param {string} description
 * @param {string} userId
 * @return {Promise<{result: boolean, msg: string, groupId: string}>}
 */
export const createGroup = async (name, description, userId) => 
  createRequestFunction('createGroup', 'POST', {name, description, userId})()

/**
 * Get all groups
 * @return {Promise<{result: boolean, msg: string, groups: {GroupObjects}}>}
 */
export const getAllGroups = async (options = {}) => 
  createRequestFunction('getAllGroups', 'GET', Object.keys(options).length ? options : undefined)()
/**
 * Join group
 * @param {string} userId
 * @param {string} groupId
 * @return {Promise<{result: boolean, msg: string}>}
 */
export const joinGroup = async (userId, groupId) => 
  createRequestFunction('joinGroup', 'POST', {userId, groupId})()

/**
 * get all groups a user is in
 * @param {string} userId
 **/
export const getGroupsAPI = async (userId, options = {}) => 
  createRequestFunction('getAllUserGroups', 'POST', {userId, ...options})()

/**
 * get all the groups events
 * @param {string} groupId
 * @return {Promise<{result: boolean, msg: string, events: {EventObjects}}>}
 */
export const getGroupEvents = async (groupId) => 
  createRequestFunction('getGroupEvents', 'POST', {groupId})()

export const getGroupChatMessages = async (groupId, userId) =>
  createRequestFunction('getGroupChatMessages', 'POST', { groupId, userId })()

export const sendGroupChatMessage = async (groupId, userId, body) =>
  createRequestFunction('sendGroupChatMessage', 'POST', { groupId, userId, body })()

export const saveEvent = async (userId, eventId) =>
  createRequestFunction('saveEvent', 'POST', { userId, eventId })()

export const removeSavedEvent = async (userId, eventId) =>
  createRequestFunction('removeSavedEvent', 'DELETE', { userId, eventId })()

export const getSavedEvents = async (userId, options = {}) =>
  createRequestFunction('getSavedEvents', 'POST', { userId, ...options })()

export const getPlanningEvents = async (userId, options = {}) =>
  createRequestFunction('getPlanningEvents', 'POST', { userId, ...options })()

export const getNotifications = async (userId) =>
  createRequestFunction('getNotifications', 'POST', { userId })()

export const markNotificationsRead = async (userId, notificationIds = [], markAll = false) =>
  createRequestFunction('markNotificationsRead', 'POST', { userId, notificationIds, markAll })()

export const getEventExportUrl = (eventId) => getUrl(`exportEventIcs?eventId=${encodeURIComponent(eventId)}`);

export const getScheduleExportUrl = (userId) => getUrl(`exportScheduleIcs?userId=${encodeURIComponent(userId)}`);

/**
 * get all the groups events for a user
 * @param {string} userId
 * @return {Promise<{result: boolean, msg: string, events: {EventObjects}}>}
 */
export const getUserGroupEvents = async (userId) => 
  createRequestFunction('getAllUserGroupEvents', 'POST', {userId})()

/** 
 * get all the image urls for an event
 * @param {string} eventId
 * @return {Promise<{result: boolean, imageUrls: [strings]}>}
 */
export const getEventImages = async (eventId) => 
  createRequestFunction('getEventImgs', 'POST', {eventId})()


  /**
 * Request to upload an event image.
 * @param {File} file - The image file to be uploaded.
 * @param {string} eventId - The ID of the event.
 * @return {Promise<{result: boolean, msg: string}>}
 */
export const uploadEventImage = async (file, eventId) => {
  // Create a FormData object to hold the file and event ID
  const formData = new FormData();
  formData.append('file', file);
  formData.append('eventId', eventId);

  try {
    const response = await fetch(getUrl('uploadEventImage'), {
      method: 'POST',
      body: formData,
    });

    const textResponse = await response.text(); // Assuming response is plain text

    if (!response.ok) {
      // If the response status code is not OK, throw an error with the response text
      throw new Error(textResponse);
    }

    // If response is OK, return an object indicating success and include the response text
    return { result: true, msg: textResponse };
  } catch (error) {
    // If fetch fails or the response status code is not OK, return an object indicating failure
    return { result: false, msg: error.message };
  }
};

/**
 * delete event 
 * @param {string} eventId
 * @param {string} userId
 * @return {Promise<{result: boolean, msg: string, evnetId: string}>}
 */
export const deleteEvent = async (eventId, userId) =>
  createRequestFunction('deleteEvent', 'DELETE', {eventId, userId})()


/**
 * delete group
 * @pararm {string} groupId
 * @param {string} userId
 * @return {Promise<{result: boolean, msg: string, groupId: string}>}
 */
export const deleteGroup = async (groupId, userId) =>
  createRequestFunction('deleteGroup', 'DELETE', {groupId, userId})()

/**
 * search for an event usinig its name
 * @param {string} name
 * @return {Promise<{result: boolean, msg: string, events: [{EventObjects}]}>}
 */
export const searchEvent = async (name) =>
  createRequestFunction('searchEvent', 'POST', {name})()


/**
 * get all the events and the attendees
 * @return {Promise<{result: boolean, msg: string, eventAttendees: [{EventObjects}]}>}
 */
 export const getEventAttendees = async () =>
  createRequestFunction('getEventAttendees', 'GET')()
  
