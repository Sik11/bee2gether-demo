import { reactive } from "vue";
import { getNotifications, markNotificationsRead } from "../api";
import { auth } from "./auth";

export const notifications = reactive({
  items: [],
  unreadCount: 0,
  loading: false,
});

export async function refreshNotifications() {
  if (!auth.isLoggedIn || !auth.user?.userId) {
    notifications.items = [];
    notifications.unreadCount = 0;
    return;
  }

  notifications.loading = true;
  try {
    const response = await getNotifications(auth.user.userId);
    if (response.result) {
      notifications.items = response.notifications || [];
      notifications.unreadCount = response.unreadCount || 0;
    } else if ((response.msg || '').toLowerCase().includes('user not found')) {
      notifications.items = [];
      notifications.unreadCount = 0;
      await auth.recoverMissingUser();
    }
  } catch (error) {
    console.error(error);
  } finally {
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
