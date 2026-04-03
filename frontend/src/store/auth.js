import { reactive } from "vue";
import { continueAsGuest as continueAsGuestAPI, createUser, loginUser } from "../api";

const STORAGE_KEY = "bee2gether.auth";
const GUEST_STORAGE_KEY = "bee2gether.guestSession";

function loadStoredAuth() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (parsed?.isLoggedIn && parsed?.user?.username) {
      return parsed;
    }
  } catch (error) {
    console.warn("Failed to restore auth state", error);
  }
  return null;
}

function persistAuthState(state) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
      user: state.user,
      isLoggedIn: state.isLoggedIn,
    }));
  } catch (error) {
    console.warn("Failed to persist auth state", error);
  }
}

function clearAuthState() {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.warn("Failed to clear auth state", error);
  }
}

function getGuestSessionId() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const existing = window.localStorage.getItem(GUEST_STORAGE_KEY);
    if (existing) {
      return existing;
    }
    const nextId = window.crypto?.randomUUID?.() || `guest-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
    window.localStorage.setItem(GUEST_STORAGE_KEY, nextId);
    return nextId;
  } catch (error) {
    console.warn("Failed to get guest session id", error);
  }
  return null;
}

const initialState = {
  user: {
    username: 'PLEASELOGIN'
  },
  isLoggedIn: false
};

const restoredState = loadStoredAuth();
let recoveryPromise = null;

/**
 * 
 */
export const auth = reactive({
  ...(restoredState ?? initialState),

  /**
   * Attempt to register the account details
   * @param {string} username
   * @param {string} password
   * @return {Promise<{result: boolean, msg: string}>}
   */
  async register(username, password) {
    try {
      const { result, msg, userId } = await createUser(username, password);
      if (result && userId) {
        auth.user = { username, userId, isGuest: false };
        auth.isLoggedIn = true;
        persistAuthState(auth);
        return { result, msg };
      } else {
        return { result: false, msg: msg || 'Registration failed' };
      }
    } catch (err) {
      console.error(err);
      return { result: false, msg: err.message };
    }
  },

  /**
   * Attempt to login
   * @param {string} username
   * @param {string} password
   */
  async login(username, password) {
    try {
      const { result, msg, userId } = await loginUser(username, password);
      if (result && userId) {
        auth.user = { username, userId, isGuest: false };
        auth.isLoggedIn = true;
        persistAuthState(auth);
        return { result, msg };
      } else {
        return { result: false, msg: msg || 'Login failed' };
      }
    } catch (err) {
      console.error(err);
      return { result: false, msg: err.message };
    }
  },

  async continueAsGuest() {
    try {
      const guestSessionId = getGuestSessionId();
      if (!guestSessionId) {
        return { result: false, msg: "Guest session unavailable" };
      }

      const { result, msg, userId, username, isGuest } = await continueAsGuestAPI(guestSessionId);
      if (result && userId && username) {
        auth.user = { username, userId, isGuest: Boolean(isGuest), guestSessionId };
        auth.isLoggedIn = true;
        persistAuthState(auth);
        return { result, msg };
      }
      return { result: false, msg: msg || "Guest login failed" };
    } catch (err) {
      console.error(err);
      return { result: false, msg: err.message };
    }
  },

  async recoverMissingUser() {
    if (recoveryPromise) {
      return recoveryPromise;
    }

    recoveryPromise = (async () => {
      if (auth.user?.isGuest) {
        try {
          const guestSessionId = auth.user?.guestSessionId || getGuestSessionId();
          if (guestSessionId) {
            const { result, userId, username, isGuest } = await continueAsGuestAPI(guestSessionId);
            if (result && userId && username) {
              auth.user = { username, userId, isGuest: Boolean(isGuest), guestSessionId };
              auth.isLoggedIn = true;
              persistAuthState(auth);
              return { recovered: true };
            }
          }
        } catch (err) {
          console.error(err);
        }
      }

      auth.logout();
      return { recovered: false };
    })().finally(() => {
      recoveryPromise = null;
    });

    return recoveryPromise;
  },

  /**
   * Logout
   */
  logout() {
    Object.assign(auth, initialState);
    clearAuthState();
  },
});
