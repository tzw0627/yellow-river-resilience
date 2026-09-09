import { computed, ref, shallowRef } from "vue";
import type { QueryGrid } from "../config/types";

export type RainfallMode = "daily" | "rolling3";

export interface EmergencyStation {
  id: string;
  name: string;
  province: string;
  lat: number;
  lon: number;
  elevation: number;
  historyStart: number | null;
  historyEnd: number | null;
  wetDayP95: number;
  wetDayP99: number;
}

export interface EmergencyObservation {
  stationId: string;
  rainfall: number;
  rolling3: number;
  percentile: number;
  level: string;
}

export interface EmergencyDay {
  date: string;
  peak: number;
  max3Day: number;
  mean: number;
  rainstormStations: number;
  affectedStations: number;
  level: string;
  observations: EmergencyObservation[];
}

export interface EmergencyEvent {
  id: string;
  date: string;
  label: string;
  source: string;
  peak: number;
  max3Day: number;
  rainstormStations: number;
}

export interface EmergencyDataset {
  metadata: {
    title: string;
    source: string;
    observationYear: number;
    historyRange: string;
    temporalResolution: string;
    stationCount: number;
    longTermStationCount: number;
    scope: string;
    usage: string;
    limitation: string;
  };
  stations: EmergencyStation[];
  events: EmergencyEvent[];
  days: EmergencyDay[];
}

export const emergencyDataset = shallowRef<EmergencyDataset | null>(null);
export const emergencyFriGrid = shallowRef<QueryGrid | null>(null);
export const emergencyLoading = ref(false);
export const emergencyError = ref("");
export const emergencyActive = ref(false);
export const selectedEmergencyDate = ref("");
export const rainfallMode = ref<RainfallMode>("daily");

export const selectedEmergencyDay = computed(() =>
  emergencyDataset.value?.days.find((item) => item.date === selectedEmergencyDate.value) ?? null,
);

export const emergencyMapStations = computed(() => {
  const data = emergencyDataset.value;
  const day = selectedEmergencyDay.value;
  if (!data || !day || !emergencyActive.value) return [];
  const stationMap = new Map(data.stations.map((station) => [station.id, station]));
  return day.observations.flatMap((observation) => {
    const station = stationMap.get(observation.stationId);
    if (!station) return [];
    const fri = sampleGrid(emergencyFriGrid.value, station.lon, station.lat) ?? 0;
    const value = rainfallMode.value === "rolling3" ? observation.rolling3 : observation.rainfall;
    const hazard = Math.min(1, value / (rainfallMode.value === "rolling3" ? 150 : 100));
    const friNormalized = Math.min(1, Math.max(0, fri / 0.72));
    const composite = Math.round(hazard * (0.55 + 0.45 * friNormalized) * 100);
    const riskLevel = composite >= 75 ? "极高" : composite >= 55 ? "高" : composite >= 35 ? "中" : "低";
    return [{
      id: station.id,
      name: station.name,
      lon: station.lon,
      lat: station.lat,
      value,
      percentile: observation.percentile,
      mode: rainfallMode.value,
      fri,
      composite,
      riskLevel,
    }];
  });
});

function sampleGrid(grid: QueryGrid | null, lon: number, lat: number) {
  if (!grid) return null;
  const { west, south, east, north } = grid.bounds;
  if (lon < west || lon > east || lat < south || lat > north) return null;
  const x = Math.round(((lon - west) / (east - west)) * (grid.width - 1));
  const y = Math.round(((north - lat) / (north - south)) * (grid.height - 1));
  return grid.values[y]?.[x] ?? null;
}

export async function loadEmergencyDataset() {
  if (emergencyDataset.value) return emergencyDataset.value;
  emergencyLoading.value = true;
  emergencyError.value = "";
  try {
    const [response, friResponse] = await Promise.all([
      fetch("/data/emergency/precipitation_2020.json"),
      fetch("/data/query_grids/four_dim/four_dim_fri_2020.json"),
    ]);
    if (!response.ok) throw new Error("实测降水数据加载失败");
    if (!friResponse.ok) throw new Error("洪水风险指数数据加载失败");
    emergencyFriGrid.value = await friResponse.json() as QueryGrid;
    emergencyDataset.value = await response.json() as EmergencyDataset;
    selectedEmergencyDate.value = emergencyDataset.value.events[0]?.date ?? emergencyDataset.value.days[0]?.date ?? "";
    return emergencyDataset.value;
  } catch (error) {
    emergencyError.value = error instanceof Error ? error.message : String(error);
    throw error;
  } finally {
    emergencyLoading.value = false;
  }
}

export function selectEmergencyEvent(date: string) {
  selectedEmergencyDate.value = date;
}
