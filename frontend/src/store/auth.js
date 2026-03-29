import { reactive } from "vue";
import { createUser, loginUser } from "../api";

const initialState = {
  user: {
    username: 'PLEASELOGIN'
  },
  isLoggedIn: false
};

/**
 * 
 */
export const auth = reactive({
  ...initialState,

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
        console.log(auth.user)
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
  },
});
