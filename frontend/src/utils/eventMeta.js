export function parseEventDate(value) {
  const raw = typeof value === "object" && value !== null
    ? value.startTime || value.time
    : value;
  if (!raw) {
    return null;
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date;
}

export function formatEventDate(value) {
  const date = parseEventDate(value);
  if (!date) {
    return typeof value === "string" ? String(value) : "Date pending";
  }

  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatEventTimeRange(event) {
  const start = parseEventDate(event);
  if (!start) {
    return "Time pending";
  }

  const end = parseEventDate(event?.endTime);
  const formatter = new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
  if (!end) {
    return formatter.format(start);
  }
  return `${formatter.format(start)} - ${formatter.format(end)}`;
}

export function formatEventDay(event) {
  const start = parseEventDate(event);
  if (!start) {
    return "Date pending";
  }
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  }).format(start);
}

export function formatEventDateWithRange(event) {
  const start = parseEventDate(event);
  if (!start) {
    return "Date pending";
  }

  return `${formatEventDay(event)} · ${formatEventTimeRange(event)}`;
}

export function toLocalDateKey(value) {
  const date = parseEventDate(value);
  if (!date) {
    return "";
  }
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function calculateDistanceMiles(origin, target) {
  if (!origin || !target) {
    return null;
  }

  const lat1 = Number(origin.lat);
  const lon1 = Number(origin.lng ?? origin.long);
  const lat2 = Number(target.lat);
  const lon2 = Number(target.lng ?? target.long);
  if (![lat1, lon1, lat2, lon2].every(Number.isFinite)) {
    return null;
  }

  const toRadians = (value) => (value * Math.PI) / 180;
  const earthRadiusMiles = 3958.8;
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return earthRadiusMiles * c;
}

export function formatDistanceLabel(origin, target) {
  const miles = calculateDistanceMiles(origin, target);
  if (miles == null) {
    return "Distance unavailable";
  }
  if (miles < 0.2) {
    return "Nearby";
  }
  return `${miles.toFixed(miles < 10 ? 1 : 0)} mi away`;
}
