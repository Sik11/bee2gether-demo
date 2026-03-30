import { reactive } from "vue";
import { createUser, loginUser } from "../api";

const STORAGE_KEY = "bee2gether.auth";

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

const initialState = {
  user: {
    username: 'PLEASELOGIN'
  },
  isLoggedIn: false
};

const restoredState = loadStoredAuth();

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
        auth.user = { username, userId };
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
        auth.user = { username, userId };
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

  /**
   * Logout
   */
  logout() {
    Object.assign(auth, initialState);
    clearAuthState();
  },
});
