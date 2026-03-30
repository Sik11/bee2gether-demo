import { createRouter, createWebHistory } from "vue-router";
import Wrapper from "./components/helper/Wrapper.vue";
import Auth from "./components/Auth.vue";
import { auth } from "./store/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/auth",
      name: "auth",
      component: Auth,
      meta: { public: true },
    },
    {
      path: "/",
      component: Wrapper,
      meta: { requiresAuth: true },
      children: [
        { path: "", redirect: "/map" },
        { path: "map", name: "map", component: () => import("./components/Map.vue") },
        { path: "events", name: "events", component: () => import("./components/YourEvents.vue") },
        { path: "groups", name: "groups", component: () => import("./components/YourGroups.vue") },
        { path: "account", name: "account", component: () => import("./components/Account.vue") },
      ],
    },
  ],
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: "auth" };
  }
  if (to.name === "auth" && auth.isLoggedIn) {
    return { name: "map" };
  }
  return true;
});

export default router;
