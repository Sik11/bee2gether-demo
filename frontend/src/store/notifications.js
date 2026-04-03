import { reactive } from "vue";
import { getNotifications, markNotificationsRead } from "../api";
import { auth } from "./auth";

export const notifications = reactive({
  items: [],
  unreadCount: 0,
  loading: false,
  hasLoaded: false,
});

const NOTIFICATIONS_CACHE_MS = 12000;
let notificationsSnapshot = null;
let notificationsRequest = null;

export async function refreshNotifications() {
  if (!auth.isLoggedIn || !auth.user?.userId) {
    notifications.items = [];
    notifications.unreadCount = 0;
    notifications.hasLoaded = false;
    return;
  }

  const now = Date.now();
  if (notificationsRequest?.userId === auth.user.userId) {
    return notificationsRequest.promise;
  }
  if (
    notificationsSnapshot?.userId === auth.user.userId
    && now - notificationsSnapshot.at < NOTIFICATIONS_CACHE_MS
  ) {
    return { result: true, notifications: notifications.items, unreadCount: notifications.unreadCount, msg: 'Using cached notifications' };
  }

  notifications.loading = true;
  try {
    const requestPromise = getNotifications(auth.user.userId);
    notificationsRequest = { userId: auth.user.userId, promise: requestPromise };
    const response = await requestPromise;
    if (response.result) {
      notifications.items = response.notifications || [];
      notifications.unreadCount = response.unreadCount || 0;
      notificationsSnapshot = { userId: auth.user.userId, at: Date.now() };
      notifications.hasLoaded = true;
    } else if ((response.msg || '').toLowerCase().includes('user not found')) {
      notifications.items = [];
      notifications.unreadCount = 0;
      notifications.hasLoaded = false;
      await auth.recoverMissingUser();
    }
    return response;
  } catch (error) {
    if (auth.isLoggedIn && auth.user?.userId) {
      console.error(error);
    }
    return { result: false, msg: error.message };
  } finally {
    notificationsRequest = null;
    notifications.loading = false;
  }
}

export async function markAllNotificationsRead() {
  if (!auth.user?.userId) {
    return;
  }
  const response = await markNotificationsRead(auth.user.userId, [], true);
  if (response.result) {
    await refreshNotifications();
  }
}

export function resetNotificationsState() {
  notifications.items = [];
  notifications.unreadCount = 0;
  notifications.loading = false;
  notifications.hasLoaded = false;
  notificationsSnapshot = null;
  notificationsRequest = null;
}
