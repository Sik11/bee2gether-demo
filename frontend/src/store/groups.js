import { reactive } from 'vue';
import { getAllGroups, createGroup, joinGroup, getGroupsAPI } from '../api';
import { auth } from '../store/auth';

// an object containing groups this user has access to
export const groups = reactive({
    availableGroups: [],
    userGroups: [],
    currentGroup: {
        name: '',
    },
    currentGroupIdForEvents: null
});

export async function updateUserGroups(userId){
    try {
        const response = await getGroupsAPI(userId);
        if (response.result) {
            getGroups().userGroups=response.memberGroups // Replace with your actual method to update groups in your application state
        } else {
            console.error(response.msg || 'Failed to get user events');
        }
    } catch (error) {
        console.error(error.message);
    }
}

export async function updateCurrentGroup(groupId){
    try {
        const response = await getAllGroups();
        if (response.result) {
            getGroups().currentGroup=response.groups.find(group => group.id === groupId)
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
            getGroups().availableGroups=response.groups
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
            getGroups().availableGroups= response.groups  // Replace with your actual method to update groups in your application state
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
    if (!auth.isLoggedIn) {
        // Wait for 5 seconds and then call the function again
        setTimeout(startPollingUserGroups, 5000);
        return;
    }

    getGroupsAPI(auth.user.userId)
        .then((response) => {
            if (response.result) {
                // Assuming you have a function or a state to update user-specific groups
                getGroups().userGroups = response.memberGroups; // Replace with your actual method to update groups in your application state
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

