import type { Bounds } from "./types";

export type ServiceScenario = "governance" | "teaching";

export type RegionGeometry =
  | { type: "Polygon"; coordinates: number[][][] }
  | { type: "MultiPolygon"; coordinates: number[][][][] };

export interface RegionBoundaryProperties {
  Name?: string;
  AdminCode?: string;
  CityName?: string;
  CityAdCode?: string;
  ProName?: string;
  [key: string]: unknown;
}

export interface RegionBoundaryFeature {
  type: "Feature";
  properties: RegionBoundaryProperties;
  geometry: RegionGeometry | null;
}

export interface RegionBoundaryCollection {
  type: "FeatureCollection";
  features: RegionBoundaryFeature[];
}

export interface RegionCase {
  id: string;
  city: string;
  province: string;
  name: string;
  segment: string;
  adminCode: string;
  bounds: Bounds;
  center: [number, number];
  feature: RegionBoundaryFeature | null;
}

export interface RegionMetricStat {
  count: number;
  mean: number | null;
  median: number | null;
  p90: number | null;
  min: number | null;
  max: number | null;
}

export interface RegionRank {
  rank_asc: number;
  rank_desc: number;
  percentile: number;
  value: number;
  count: number;
}

export interface RegionAnalysis {
  id: string;
  name: string;
  city: string;
  province: string;
  bounds: Bounds;
  stats: Record<string, Record<string, RegionMetricStat>>;
  derived: Record<string, number | null>;
  ranks: Record<string, RegionRank>;
}

export interface RegionAnalysisFile {
  metadata: {
    source: string;
    years: number[];
    layers: string[];
    thresholds: Record<string, number>;
  };
  regions: Record<string, RegionAnalysis>;
}

export const CASE_LAYERS = ["four_dim_fri", "four_dim_er", "four_dim_erd"];

export const DEFAULT_REGION_CASE: RegionCase = {
  id: "study-area",
  city: "研究区",
  province: "",
  name: "黄河滩区中下游边界",
  segment: "黄河滩区",
  adminCode: "",
  bounds: { west: 112.177287, south: 34.237112, east: 116.678382, north: 36.454202, center: [114.427835, 35.345657] },
  center: [114.427835, 35.345657],
  feature: null,
};

const CITY_ORDER = ["郑州市", "新乡市", "开封市", "焦作市", "濮阳市", "洛阳市", "菏泽市", "济宁市", "泰安市"];

function flattenPositions(geometry: RegionGeometry | null): [number, number][] {
  if (!geometry) return [];
  if (geometry.type === "Polygon") {
    return geometry.coordinates.flatMap((ring) => ring.map((position) => [position[0], position[1]] as [number, number]));
  }
  return geometry.coordinates.flatMap((polygon) =>
    polygon.flatMap((ring) => ring.map((position) => [position[0], position[1]] as [number, number])),
  );
}

export function boundsFromRegionFeature(feature: RegionBoundaryFeature): Bounds {
  const positions = flattenPositions(feature.geometry);
  if (!positions.length) return DEFAULT_REGION_CASE.bounds;
  const xs = positions.map(([lon]) => lon);
  const ys = positions.map(([, lat]) => lat);
  const west = Math.min(...xs);
  const east = Math.max(...xs);
  const south = Math.min(...ys);
  const north = Math.max(...ys);
  const center: [number, number] = [(west + east) / 2, (south + north) / 2];
  return { west, south, east, north, center };
}

function segmentFor(city: string): string {
  return city ? city.replace(/市$/, "段") : "黄河滩区";
}

function citySortValue(city: string) {
  const index = CITY_ORDER.indexOf(city);
  return index === -1 ? CITY_ORDER.length : index;
}

export function regionCasesFromBoundary(collection: RegionBoundaryCollection | null): RegionCase[] {
  const features = collection?.features ?? [];
  return features
    .filter((feature) => feature.geometry)
    .map((feature, index) => {
      const props = feature.properties ?? {};
      const name = String(props.Name ?? `区域${index + 1}`);
      const city = String(props.CityName ?? "未分组");
      const province = String(props.ProName ?? "");
      const adminCode = String(props.AdminCode ?? `${city}-${name}-${index}`);
      const bounds = boundsFromRegionFeature(feature);
      return {
        id: adminCode,
        city,
        province,
        name,
        segment: segmentFor(city),
        adminCode,
        bounds,
        center: bounds.center ?? [(bounds.west + bounds.east) / 2, (bounds.south + bounds.north) / 2],
        feature,
      };
    })
    .sort(
      (a, b) =>
        citySortValue(a.city) - citySortValue(b.city) ||
        a.city.localeCompare(b.city, "zh-Hans-CN") ||
        a.name.localeCompare(b.name, "zh-Hans-CN"),
    );
}
