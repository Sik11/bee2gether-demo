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

/**
 * Get the string url for that path with client Id.
 * @param {string} path - The commands path.
 * @param {string} clientId - The id of the user making the request, defaults to 'default'.
 * @returns {string} A string url to make a request to.
 */
const getUrl = (path, clientId = "default") => {
  const apiRoot = API_ENDPOINT.startsWith("http")
    ? API_ENDPOINT
    : new URL(API_ENDPOINT, window.location.origin).toString();
  const url = new URL(`${path}`, apiRoot.endsWith("/") ? apiRoot : `${apiRoot}/`);
  url.searchParams.set("code", CODE);
  url.searchParams.set("clientId", clientId);
  return url.toString();
};

/**
 * Helper function to create a request function.
 * @param {string} path - The path for the request.
 * @param {string} method - The HTTP method for the request.
 * @param {Object} requestBody - The request body as an object.
 * @returns {function} A function that makes the request.
 */
const createRequestFunction = (path, method, requestBody=undefined) => async () =>
  new Promise((resolve, reject) =>
    fetch(getUrl(path), {
      method,
      body: JSON.stringify(requestBody),
      headers: {
        'Content-Type': 'application/json',
      }
    })
      .then((response) => response.json())
      .then((data) => resolve(data))
      .catch((error) => reject(error))
  );

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
export const attendingEvents = async (userId) => 
  createRequestFunction('getAttendingEvents', 'POST', {userId})()

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
export const getAllGroups = async () => 
  createRequestFunction('getAllGroups', 'GET')()
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
export const getGroupsAPI = async (userId) => 
  createRequestFunction('getAllUserGroups', 'POST', {userId})()

/**
 * get all the groups events
 * @param {string} groupId
 * @return {Promise<{result: boolean, msg: string, events: {EventObjects}}>}
 */
export const getGroupEvents = async (groupId) => 
  createRequestFunction('getGroupEvents', 'POST', {groupId})()

export const saveEvent = async (userId, eventId) =>
  createRequestFunction('saveEvent', 'POST', { userId, eventId })()

export const removeSavedEvent = async (userId, eventId) =>
  createRequestFunction('removeSavedEvent', 'DELETE', { userId, eventId })()

export const getSavedEvents = async (userId) =>
  createRequestFunction('getSavedEvents', 'POST', { userId })()

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
  
