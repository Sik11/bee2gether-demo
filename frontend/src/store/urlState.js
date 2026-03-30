function hasWindow() {
  return typeof window !== "undefined";
}

export function readQueryState() {
  if (!hasWindow()) {
    return { tab: null, event: null, group: null };
  }

  const params = new URLSearchParams(window.location.search);
  return {
    tab: params.get("tab"),
    event: params.get("event"),
    group: params.get("group"),
  };
}

export function updateQueryState(patch) {
  if (!hasWindow()) {
    return;
  }

  const url = new URL(window.location.href);
  for (const [key, value] of Object.entries(patch)) {
    if (value === null || value === undefined || value === "") {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, String(value));
    }
  }

  const next = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState({}, "", next);
}
