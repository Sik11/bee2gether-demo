export function formatEventDate(value) {
  if (!value) {
    return "Date pending";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
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
