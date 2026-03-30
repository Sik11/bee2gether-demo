export function readQueryState() {
  const route = globalThis?.__beeRouter?.currentRoute?.value;
  const params = route?.query ?? {};
  return {
    tab: params.tab ?? null,
    event: params.event ?? null,
    group: params.group ?? null,
    notifications: params.notifications ?? null,
  };
}

export function updateQueryState(patch) {
  const router = globalThis?.__beeRouter;
  const route = router?.currentRoute?.value;
  if (!router || !route) return;
  const query = { ...route.query };
  for (const [key, value] of Object.entries(patch)) {
    if (value === null || value === undefined || value === "") {
      delete query[key];
    } else {
      query[key] = String(value);
    }
  }
  router.replace({ query });
}
