export const regionLabels = [
  { name: "洛阳段", lon: 112.38, lat: 34.96 },
  { name: "焦温孟郑州段", lon: 113.02, lat: 34.98 },
  { name: "新乡段", lon: 114.28, lat: 35.18 },
  { name: "濮阳段", lon: 115.72, lat: 35.88 },
];

export const stations = [
  { name: "孟津", lon: 112.43, lat: 34.83 },
  { name: "孟州", lon: 112.78, lat: 34.92 },
  { name: "温县", lon: 113.08, lat: 34.95 },
  { name: "巩义", lon: 112.97, lat: 34.73 },
  { name: "原阳", lon: 113.95, lat: 35.05 },
  { name: "封丘", lon: 114.43, lat: 35.05 },
  { name: "长垣", lon: 114.67, lat: 35.2 },
  { name: "台前", lon: 115.87, lat: 35.98 },
];

export function nearestStation(lon: number, lat: number) {
  let best: (typeof stations)[number] | null = null;
  let bestDistance = Infinity;
  for (const station of stations) {
    const dx = (lon - station.lon) * Math.cos((lat * Math.PI) / 180);
    const dy = lat - station.lat;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = station;
    }
  }
  return best;
}
