import { reactive } from 'vue';
import { getAllGroups, createGroup, joinGroup, getGroupsAPI } from '../api';
import { auth } from '../store/auth';
import { pages } from './pages';
import { updateQueryState } from './urlState';

// an object containing groups this user has access to
export const groups = reactive({
    availableGroups: [],
    userGroups: [],
    availableGroupsTotal: 0,
    userGroupsTotal: 0,
    loadingAvailableGroups: false,
    loadingUserGroups: false,
    hasLoadedAvailableGroups: false,
    hasLoadedUserGroups: false,
    currentGroup: {
        name: '',
    },
    currentGroupIdForEvents: null,
    selectGroup(group, options = {}) {
        const { openLayer = true, syncUrl = true } = options;
        groups.currentGroup = group;
        if (openLayer && !pages.layers.includes('group-overview')) {
            pages.addLayer('group-overview');
        }
        if (syncUrl) {
            updateQueryState({ group: group?.id ?? null, event: null, tab: pages.selected });
        }
    },
    async selectGroupById(groupId, options = {}) {
        if (!groupId) {
            return null;
        }
        let group = groups.availableGroups.find((entry) => entry.id === groupId)
          || groups.userGroups.find((entry) => entry.id === groupId);
        if (!group) {
            await updateGroups();
            group = groups.availableGroups.find((entry) => entry.id === groupId);
        }
        if (!group) {
            return null;
        }
        groups.selectGroup(group, options);
        return group;
    },
    clearSelectedGroup(options = {}) {
        const { syncUrl = true } = options;
        groups.currentGroup = { name: '' };
        if (syncUrl) {
            updateQueryState({ group: null });
        }
    }
});

const ALL_GROUPS_POLL_INTERVAL_MS = 15000;
const USER_GROUPS_POLL_INTERVAL_MS = 15000;
const ALL_GROUPS_CACHE_MS = 12000;
const USER_GROUPS_CACHE_MS = 12000;
let allGroupsPollingStarted = false;
let allGroupsPollInFlight = false;
let userGroupsPollingStarted = false;
let userGroupsPollInFlight = false;

function isDocumentHidden() {
    return typeof document !== 'undefined' && document.hidden;
}

function isAuthRoute() {
    return typeof window !== 'undefined' && window.location.pathname === '/auth';
}

function normalizeGroup(group) {
    if (!group) {
        return group;
    }

    const events = Array.isArray(group.events) ? group.events : [];
    const memberIds = Array.isArray(group.memberIds) ? group.memberIds : [];
    const memberCount = typeof group.memberCount === 'number' ? group.memberCount : memberIds.length;
    const upcomingEventCount = typeof group.upcomingEventCount === 'number'
        ? group.upcomingEventCount
        : events.length;

    return {
        ...group,
        memberCount,
        upcomingEventCount,
    };
}

function normalizeGroups(collection) {
    return Array.isArray(collection) ? collection.map(normalizeGroup) : [];
}

export async function updateUserGroups(userId, options = {}){
    if (!userId) {
        getGroups().userGroups = [];
        getGroups().userGroupsTotal = 0;
        groups.hasLoadedUserGroups = false;
        return { result: false, msg: 'UserId is required' };
    }
    const offset = Number(options.offset || 0);
    const limit = Number(options.limit || 5);
    const now = Date.now();
    if (groups._userGroupsRequest?.key === `${userId}:${offset}:${limit}`) {
        return groups._userGroupsRequest.promise;
    }
    if (
        groups._userGroupsSnapshot?.key === `${userId}:${offset}:${limit}`
        && now - groups._userGroupsSnapshot.at < USER_GROUPS_CACHE_MS
    ) {
        return { result: true, memberGroups: getGroups().userGroups, msg: 'Using cached user groups' };
    }
    groups.loadingUserGroups = true;
    try {
        const requestPromise = getGroupsAPI(userId, { offset, limit });
        groups._userGroupsRequest = { key: `${userId}:${offset}:${limit}`, promise: requestPromise };
        const response = await requestPromise;
        if (response.result) {
            getGroups().userGroups = normalizeGroups(response.memberGroups);
            getGroups().userGroupsTotal = Number(response.total ?? getGroups().userGroups.length);
            groups._userGroupsSnapshot = { key: `${userId}:${offset}:${limit}`, at: Date.now() };
            groups.hasLoadedUserGroups = true;
        } else {
            if ((response.msg || '').toLowerCase().includes('user not found')) {
                getGroups().userGroups = [];
                await auth.recoverMissingUser();
                return response;
            }
            console.error(response.msg || 'Failed to get user events');
        }
        return response;
    } catch (error) {
        if (auth.isLoggedIn && auth.user?.userId) {
            console.error(error.message);
        }
        return { result: false, msg: error.message };
    } finally {
        groups.loadingUserGroups = false;
        if (groups._userGroupsRequest?.key === `${userId}:${offset}:${limit}`) {
            groups._userGroupsRequest = null;
        }
    }
}

export async function updateCurrentGroup(groupId){
    try {
        const response = await getAllGroups();
        if (response.result) {
            getGroups().currentGroup = normalizeGroup(response.groups.find(group => group.id === groupId))
        } else {
            console.error(response.msg || 'Failed to get user events');
        }
    } catch (error) {
        console.error(error.message);
    }
}


export async function updateGroups(options = {}) {
    const offset = Number(options.offset || 0);
    const limit = Number(options.limit || 5);
    const now = Date.now();
    if (groups._allGroupsRequest?.key === `${offset}:${limit}`) {
        return groups._allGroupsRequest.promise;
    }
    if (
        groups._allGroupsSnapshot?.key === `${offset}:${limit}`
        && now - groups._allGroupsSnapshot.at < ALL_GROUPS_CACHE_MS
    ) {
        return { result: true, groups: getGroups().availableGroups, msg: 'Using cached groups' };
    }
    groups.loadingAvailableGroups = true;
    try {
        const requestPromise = getAllGroups({ offset, limit });
        groups._allGroupsRequest = { key: `${offset}:${limit}`, promise: requestPromise };
        const response = await requestPromise;
        if (response.result) {
            getGroups().availableGroups = normalizeGroups(response.groups);
            getGroups().availableGroupsTotal = Number(response.total ?? getGroups().availableGroups.length);
            groups._allGroupsSnapshot = { key: `${offset}:${limit}`, at: Date.now() };
            groups.hasLoadedAvailableGroups = true;
        } else {
            console.error(response.msg || 'Failed to get user events');
        }
        return response;
    } catch (error) {
        if (!isAuthRoute()) {
            console.error(error.message);
        }
        return { result: false, msg: error.message };
    } finally {
        groups.loadingAvailableGroups = false;
        if (groups._allGroupsRequest?.key === `${offset}:${limit}`) {
            groups._allGroupsRequest = null;
        }
    }
}

// get ref to events
export function getGroups() {
    return groups;
}

export function resetGroupsState() {
    groups.loadingAvailableGroups = false;
    groups.loadingUserGroups = false;
    groups.hasLoadedAvailableGroups = false;
    groups.hasLoadedUserGroups = false;
    groups.availableGroups = [];
    groups.userGroups = [];
    groups.availableGroupsTotal = 0;
    groups.userGroupsTotal = 0;
    groups._allGroupsRequest = null;
    groups._userGroupsRequest = null;
    groups._allGroupsSnapshot = null;
    groups._userGroupsSnapshot = null;
    groups.currentGroup = { name: '' };
}
/**
 * Start polling for all groups and update application state.
 */
export function startPollingAllGroups() {
    if (allGroupsPollingStarted) {
        return;
    }
    allGroupsPollingStarted = true;

    const pollAllGroups = async () => {
        if (allGroupsPollInFlight) {
            setTimeout(pollAllGroups, ALL_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        if (pages.selected !== 'groups') {
            setTimeout(pollAllGroups, ALL_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        if (isDocumentHidden()) {
            setTimeout(pollAllGroups, ALL_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        allGroupsPollInFlight = true;
        try {
            const response = await updateGroups();
            if (response.result) {
                getGroups().availableGroups = normalizeGroups(response.groups);
            }
        } catch (error) {
            console.error('Error polling all groups:', error);
        } finally {
            allGroupsPollInFlight = false;
            setTimeout(pollAllGroups, ALL_GROUPS_POLL_INTERVAL_MS);
        }
    };

    pollAllGroups();
}

/**
 * Start polling for groups a specific user is in and update application state.
 * 
 */
export function startPollingUserGroups() {
    if (userGroupsPollingStarted) {
        return;
    }
    userGroupsPollingStarted = true;

    const pollUserGroups = async () => {
        if (userGroupsPollInFlight) {
            setTimeout(pollUserGroups, USER_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        if (!auth.isLoggedIn || !auth.user?.userId) {
            setTimeout(pollUserGroups, USER_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        if (!['groups', 'events', 'account'].includes(pages.selected)) {
            setTimeout(pollUserGroups, USER_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        if (isDocumentHidden()) {
            setTimeout(pollUserGroups, USER_GROUPS_POLL_INTERVAL_MS);
            return;
        }

        userGroupsPollInFlight = true;
        try {
            const response = await updateUserGroups(auth.user.userId);
            if (response.result) {
                getGroups().userGroups = normalizeGroups(response.memberGroups);
            } else if ((response.msg || '').toLowerCase().includes('user not found')) {
                getGroups().userGroups = [];
                await auth.recoverMissingUser();
            }
        } catch (error) {
            console.error('Error polling user groups:', error);
        } finally {
            userGroupsPollInFlight = false;
            setTimeout(pollUserGroups, USER_GROUPS_POLL_INTERVAL_MS);
        }
    };

    pollUserGroups();
}





/**
 * Adds a group and updates the application state.
 * @param {string} name - The name of the group.
 * @param {string} description - The description of the group.
 * @param {string} userId - The ID of the user creating the group.
 * @return {Promise<{result: boolean, msg: string, groupId?: string}>}
 */
export async function addGroup(name, description, userId) {
    try {
        const { result, msg, groupId } = await createGroup(name, description, userId);
        console.log("Result: " + result);
        console.log("GroupId: " + groupId);
        if (result && groupId) {
            await updateGroups();
            await updateUserGroups(userId);
            return { result, msg };
        } else {
            return { result: false, msg: msg || 'Group creation failed' };
        }
    } catch (error) {
        console.error(error);
        return { result: false, msg: error.message };
    }
}


/**
 * Joins a group and updates the application state.
 * @param {string} groupId - The ID of the group to join.
 * @return {Promise<{result: boolean, msg: string}>}
 */
export async function joinUserGroup(groupId) {
    try {
        const userId = auth.user.userId; // Assuming this is how you get the current user's ID
        const { result, msg } = await joinGroup(userId, groupId);
        console.log("Join Group Result: " + result);
        if (result) {
            await updateGroups();
            await updateUserGroups(userId);
            return { result, msg };
        } else {
            return { result: false, msg: msg || 'Failed to join group' };
        }
    } catch (error) {
        console.error("Error joining group:", error);
        return { result: false, msg: error.message };
    }
}

