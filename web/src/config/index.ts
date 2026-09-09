import { LAYER_DATA_CONFIG } from "./generated/layerDataConfig";
import { LAYER_SPATIAL_CONFIG } from "./generated/layerSpatialConfig";
import { LAYER_STATS_2024 } from "./generated/layerStats2024";
import { LAYER_STATS_ALIGNED } from "./generated/layerStatsAligned";
import type { LayerStat } from "./types";

export { LAYER_DATA_CONFIG, LAYER_SPATIAL_CONFIG };
export * from "./types";
export * from "./layerMeta";
export * from "./legend";
export * from "./places";
export * from "./regionCases";

// 补充统计：2024 与对齐年份统计叠加在 summary.timeline 之外，作为前端兜底。
export const supplementalLayerStats: Record<string, Record<string, LayerStat>> = {
  ...(LAYER_STATS_ALIGNED as unknown as Record<string, Record<string, LayerStat>>),
  ...(LAYER_STATS_2024 as unknown as Record<string, Record<string, LayerStat>>),
};

export interface SpatialBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export function spatialBounds(): SpatialBounds | null {
  const bounds = (LAYER_SPATIAL_CONFIG as { bounds?: SpatialBounds }).bounds;
  return bounds ?? null;
}

export const realDataConfig = LAYER_DATA_CONFIG as {
  sourceRoot?: string;
  displayYears?: number[];
  layers?: Record<string, RealDataLayer>;
};

export interface RealDataYearEntry {
  source?: string;
  overlay?: string;
  queryGrid?: string;
  converted?: boolean;
}

export interface RealDataLayer {
  key: string;
  label: string;
  format?: string;
  resolution?: string;
  source?: string;
  statsCsv?: string;
  sourceFolder?: string;
  converted?: boolean;
  years?: Record<string, RealDataYearEntry>;
}

export function realDataLayer(key: string): RealDataLayer | null {
  return realDataConfig.layers?.[key] ?? null;
}

export function absoluteSourceText(relativePath?: string): string {
  if (!relativePath) return "";
  const root = realDataConfig.sourceRoot || "";
  return root ? `${root}/${relativePath}` : relativePath;
}

export function realDataYearEntry(key: string, year: number | string): RealDataYearEntry | null {
  const config = realDataLayer(key);
  if (!config) return null;
  return config.years?.[String(year)] ?? null;
}

export interface Availability {
  available: boolean;
  entry: RealDataYearEntry | LayerStat | null;
  config: RealDataLayer | null;
}

/** 与旧前端 currentYearAvailability 等价的纯函数实现。 */
export function currentYearAvailabilityRaw(
  layer: string,
  year: number,
  getStat: (year: number | string, layer: string) => LayerStat | null,
): Availability {
  if (layer === "ri") return { available: year === 2025, entry: null, config: null };
  if (String(layer).startsWith("four_dim_")) {
    const stat = getStat(year, layer);
    return { available: Boolean(stat?.available), entry: stat ?? null, config: null };
  }
  const config = realDataLayer(layer);
  const entry = realDataYearEntry(layer, year);
  return {
    available: Boolean(entry && entry.converted !== false),
    entry,
    config,
  };
}
