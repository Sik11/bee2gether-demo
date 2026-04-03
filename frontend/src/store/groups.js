import { reactive } from 'vue';
import { getAllGroups, createGroup, joinGroup, getGroupsAPI } from '../api';
import { auth } from '../store/auth';
import { pages } from './pages';
import { updateQueryState } from './urlState';

// an object containing groups this user has access to
export const groups = reactive({
    availableGroups: [],
    userGroups: [],
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

export async function updateUserGroups(userId){
    if (!userId) {
        getGroups().userGroups = [];
        return { result: false, msg: 'UserId is required' };
    }
    try {
        const response = await getGroupsAPI(userId);
        if (response.result) {
            getGroups().userGroups = normalizeGroups(response.memberGroups);
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
        console.error(error.message);
        return { result: false, msg: error.message };
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


export async function updateGroups() {
    try {
        const response = await getAllGroups();
        if (response.result) {
            getGroups().availableGroups = normalizeGroups(response.groups);
        } else {
            console.error(response.msg || 'Failed to get user events');
        }
    } catch (error) {
        console.error(error.message);
    }
}

// get ref to events
export function getGroups() {
    return groups;
}
/**
 * Start polling for all groups and update application state.
 */
export function startPollingAllGroups() {
    getAllGroups()
    .then((response) => {
        if (response.result) {
            // Assuming you have a function or a state to update all available groups
            getGroups().availableGroups = normalizeGroups(response.groups);
        }
    })
    .then(() => {
        setTimeout(startPollingAllGroups, 5000); // Poll every 5 seconds
    })
    .catch((error) => {
        console.error('Error polling all groups:', error);
    });
}

/**
 * Start polling for groups a specific user is in and update application state.
 * 
 */
export function startPollingUserGroups() {
    if (!auth.isLoggedIn || !auth.user?.userId) {
        // Wait for 5 seconds and then call the function again
        setTimeout(startPollingUserGroups, 5000);
        return;
    }

    getGroupsAPI(auth.user.userId)
        .then((response) => {
            if (response.result) {
                // Assuming you have a function or a state to update user-specific groups
                getGroups().userGroups = normalizeGroups(response.memberGroups);
            } else if ((response.msg || '').toLowerCase().includes('user not found')) {
                getGroups().userGroups = [];
                return auth.recoverMissingUser();
            }
        })
        .then(() => {
            // Continue polling every 5 seconds
            setTimeout(startPollingUserGroups, 5000);
        })
        .catch((error) => {
            console.error('Error polling user groups:', error);
        });
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
            // const newGroup = { name, description, id: groupId}; // Assuming the creator is the first member
            // // Update your application's state with newGroup
            // // For example: appState.groups.push(newGroup);
            // getGroups().availableGroups.push(newGroup);
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
            // Assuming you have a method to update the user's groups in your application state
            // Here, you might need to fetch the group details or have them already available
            // const joinedGroup = groups.availableGroups.find(group => group.id === groupId);
            // if (joinedGroup) {
            //     getGroups().userGroups.push(joinedGroup);
            // }
            return { result, msg };
        } else {
            return { result: false, msg: msg || 'Failed to join group' };
        }
    } catch (error) {
        console.error("Error joining group:", error);
        return { result: false, msg: error.message };
    }
}

