import { reactive } from "vue";
import { auth } from "./auth";
import { notifications } from "./notifications";
import { events } from "./events";
import { groups, updateGroups, updateUserGroups } from "./groups";

const realtimeBus = new EventTarget();
const reconnectState = {
  timeoutId: null,
  attempt: 0,
};

export const realtime = reactive({
  status: "disconnected",
});

let socket = null;
let identifiedUserId = null;
const subscriptions = new Set();

function getRealtimeUrl() {
  const apiRoot = import.meta.env.VITE_API_BASE_URL || "/api";
  const httpUrl = apiRoot.startsWith("http")
    ? apiRoot
    : new URL(apiRoot, window.location.origin).toString();
  const endpoint = new URL(httpUrl.endsWith("/") ? `${httpUrl}realtime` : `${httpUrl}/realtime`);
  endpoint.protocol = endpoint.protocol === "https:" ? "wss:" : "ws:";
  endpoint.searchParams.set("code", import.meta.env.VITE_API_CODE || "local-demo");
  endpoint.searchParams.set("clientId", "default");
  return endpoint.toString();
}

function emitRealtimeEvent(type, detail) {
  realtimeBus.dispatchEvent(new CustomEvent(type, { detail }));
}

function upsertById(collection, entry) {
  if (!Array.isArray(collection) || !entry?.id) {
    return;
  }
  const index = collection.findIndex((item) => item.id === entry.id);
  if (index === -1) {
    collection.unshift(entry);
    return;
  }
  collection[index] = { ...collection[index], ...entry };
}

function patchEventAttendance(detail) {
  if (!detail?.eventId) {
    return;
  }

  const attendees = Array.isArray(detail.attendees) ? detail.attendees : [];
  const foundIndex = events.eventAttendees.findIndex((entry) => entry.eventId === detail.eventId);
  if (foundIndex === -1) {
    events.eventAttendees.push({ eventId: detail.eventId, attendees });
  } else {
    events.eventAttendees[foundIndex] = {
      ...events.eventAttendees[foundIndex],
      attendees,
    };
  }

  const patchList = (list) => {
    if (!Array.isArray(list)) {
      return;
    }
    const eventIndex = list.findIndex((entry) => entry.id === detail.eventId);
    if (eventIndex !== -1) {
      list[eventIndex] = {
        ...list[eventIndex],
        attendees,
      };
    }
  };

  patchList(events.availableEvents);
  patchList(events.userEvents);
  patchList(events.groupEvents);
  patchList(events.savedEvents);

  if (events.selected?.id === detail.eventId) {
    events.selected = {
      ...events.selected,
      attendees,
    };
  }
}

async function handleRealtimeMessage(message) {
  if (!message?.type) {
    return;
  }

  switch (message.type) {
    case "auth.identified":
      identifiedUserId = message.userId;
      realtime.status = "connected";
      break;
    case "notifications.updated":
      if (message.userId === auth.user?.userId) {
        notifications.items = message.notifications || [];
        notifications.unreadCount = message.unreadCount || 0;
      }
      break;
    case "group.chat.message.created":
    case "event.comment.created":
    case "event.comment.deleted":
      emitRealtimeEvent(message.type, message);
      break;
    case "event.attendance.updated":
      patchEventAttendance(message);
      emitRealtimeEvent(message.type, message);
      break;
    case "group.membership.updated":
      if (message.group && groups.currentGroup?.id === message.group.id) {
        groups.currentGroup = {
          ...groups.currentGroup,
          ...message.group,
        };
      }
      if (auth.user?.userId) {
        await updateUserGroups(auth.user.userId);
      }
      await updateGroups();
      emitRealtimeEvent(message.type, message);
      break;
    case "group.updated":
      if (message.group && groups.currentGroup?.id === message.group.id) {
        groups.currentGroup = {
          ...groups.currentGroup,
          ...message.group,
        };
      }
      await updateGroups();
      emitRealtimeEvent(message.type, message);
      break;
    default:
      break;
  }
}

function clearReconnectTimer() {
  if (reconnectState.timeoutId) {
    window.clearTimeout(reconnectState.timeoutId);
    reconnectState.timeoutId = null;
  }
}

function scheduleReconnect() {
  if (!auth.isLoggedIn || !auth.user?.userId) {
    return;
  }
  clearReconnectTimer();
  const delay = Math.min(1000 * (2 ** reconnectState.attempt), 10000);
  reconnectState.timeoutId = window.setTimeout(() => {
    reconnectState.attempt += 1;
    void connectRealtime();
  }, delay);
}

function sendSubscription(type, channel) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }
  socket.send(JSON.stringify({ type, channel }));
}

function identifySocket() {
  if (!socket || socket.readyState !== WebSocket.OPEN || !auth.user?.userId) {
    return;
  }
  socket.send(JSON.stringify({
    type: "auth.identify",
    payload: {
      userId: auth.user.userId,
      guestSessionId: auth.user.guestSessionId,
    },
  }));

  for (const channel of subscriptions) {
    sendSubscription("subscribe", channel);
  }
}

export async function connectRealtime() {
  if (typeof window === "undefined" || !auth.isLoggedIn || !auth.user?.userId) {
    return;
  }

  if (socket && [WebSocket.OPEN, WebSocket.CONNECTING].includes(socket.readyState) && identifiedUserId === auth.user.userId) {
    return;
  }

  disconnectRealtime({ clearSubscriptions: false });

  realtime.status = "connecting";
  socket = new WebSocket(getRealtimeUrl());
  socket.addEventListener("open", () => {
    reconnectState.attempt = 0;
    identifySocket();
  });
  socket.addEventListener("message", (event) => {
    try {
      void handleRealtimeMessage(JSON.parse(event.data));
    } catch (error) {
      console.error("Failed to parse realtime message", error);
    }
  });
  socket.addEventListener("close", () => {
    socket = null;
    identifiedUserId = null;
    realtime.status = "disconnected";
    scheduleReconnect();
  });
  socket.addEventListener("error", () => {
    realtime.status = "disconnected";
  });
}

export function disconnectRealtime({ clearSubscriptions = false } = {}) {
  clearReconnectTimer();
  if (clearSubscriptions) {
    subscriptions.clear();
  }
  if (socket) {
    const activeSocket = socket;
    socket = null;
    identifiedUserId = null;
    activeSocket.close();
  }
  realtime.status = "disconnected";
}

export function subscribeRealtimeChannel(channel) {
  if (!channel) {
    return;
  }
  subscriptions.add(channel);
  sendSubscription("subscribe", channel);
}

export function unsubscribeRealtimeChannel(channel) {
  if (!channel) {
    return;
  }
  subscriptions.delete(channel);
  sendSubscription("unsubscribe", channel);
}

export function addRealtimeListener(type, handler) {
  const wrappedHandler = (event) => handler(event.detail);
  realtimeBus.addEventListener(type, wrappedHandler);
  return () => {
    realtimeBus.removeEventListener(type, wrappedHandler);
  };
}
